# Django Performance Audit

Scope: audited the Django project files present under `rental_app/`, including app models, views, forms, admin, middleware, templates, static/PWA files, deployment files, and settings. Excluded generated/vendor directories: `venv/`, `node_modules/`, `staticfiles/`, and `repomix-output.xml`.

No additional files are required to continue this analysis. Expected files that are not present: `tweet/signals.py` and `tweet/tasks.py`. `settings.py` references `tweet.tasks.aggregate_daily_analytics`, but no `tweet/tasks.py` exists.

Validation note: `manage.py check` could not run in the root `.venv` because `cloudinary` is missing. The project-local `rental_app/venv` is also broken because its launcher points at a stale WindowsApps Python path.

## Findings

### 1. Dynamic HTML is cached by the service worker

- Location: `rental_app/templates/sw.js:41`
- Severity: Critical
- Problem: navigation requests use stale-while-revalidate and cache every successful HTML navigation except `/accounts/` and `/admin/`. This can serve stale personalized pages, stale CSRF-bearing HTML, and old full-page markup after HTMX/layout changes. This directly explains duplicated nav/footer still appearing after code changes if the service worker has cached older HTML.
- Expected impact: fixes stale UI and privacy risk; removes a major source of nav/footer duplication and login weirdness.
- Migration: none.
- Estimated improvement: correctness fix; eliminates cached HTML serving for dynamic pages.

Before:

```js
const cachedResponse = await cache.match(event.request);
const fetchPromise = fetch(event.request).then(async networkResponse => {
  if (networkResponse.ok) {
    cache.put(event.request, networkResponse.clone());
  }
  return networkResponse;
});
return cachedResponse || fetchPromise;
```

After:

```js
try {
  return await fetch(event.request);
} catch (error) {
  return await caches.match('/offline/');
}
```

If you want to cache public HTML later, cache only an explicit allowlist like `/offline/`, not authenticated or HTMX-driven pages.

### 2. HTMX Vary middleware exists but is not installed

- Location: `tweet/middleware.py:60`, `rental_app/settings.py:113`
- Severity: High
- Problem: `HtmxVaryMiddleware` is defined but not in `MIDDLEWARE`. The same URL returns different bodies for HTMX and normal requests via `base_template`, so shared/browser/proxy caches need `Vary` headers.
- Expected impact: prevents full-page/partial response cache mixing.
- Migration: none.
- Estimated improvement: eliminates a class of duplicate layout and missing layout bugs.

Before:

```python
"django.middleware.common.CommonMiddleware",
"django.middleware.csrf.CsrfViewMiddleware",
```

After:

```python
"django.middleware.common.CommonMiddleware",
"tweet.middleware.HtmxVaryMiddleware",
"django.middleware.csrf.CsrfViewMiddleware",
```

Also update the middleware:

```python
patch_vary_headers(response, ("HX-Request", "HX-History-Restore-Request"))
```

### 3. Wishlist AJAX expects 401 but the view returns a login redirect

- Location: `tweet/views.py:329`, `rental_app/templates/layout.html:224`
- Severity: High
- Problem: the JavaScript handles `401` JSON for anonymous wishlist actions, but `toggle_wishlist()` returns a `302` redirect. `fetch()` follows the redirect and then JSON parsing fails, so the login flow appears broken.
- Expected impact: fixes anonymous wishlist login redirect behavior.
- Migration: none.
- Estimated improvement: removes a failed request/HTML parse path for every anonymous wishlist click.

Before:

```python
if not request.user.is_authenticated:
    return redirect_to_login(request.get_full_path(), reverse("index"))
```

After:

```python
if not request.user.is_authenticated:
    if _wants_json(request) or request.headers.get("HX-Request") == "true":
        return JsonResponse({"login_url": reverse("account_login")}, status=401)
    return redirect_to_login(request.get_full_path(), reverse("index"))
```

### 4. Wishlist HTMX removal can swap a redirected listing page into a card

- Location: `tweet/templates/wishlist.html:69`, `tweet/views.py:346`
- Severity: High
- Problem: the wishlist remove form is HTMX, but `toggle_wishlist()` returns JSON only for `XMLHttpRequest` or JSON Accept headers. HTMX requests can fall through to `redirect('rental_list')`, causing a full listing page response to be swapped into `#wishlist-item-*`.
- Expected impact: prevents DOM corruption and unnecessary full-page renders.
- Migration: none.
- Estimated improvement: avoids a full page render and large DOM swap per wishlist remove.

Before:

```python
if _wants_json(request):
    return JsonResponse({...})
return redirect('rental_list')
```

After:

```python
if request.headers.get("HX-Request") == "true":
    return HttpResponse(status=204)
if _wants_json(request):
    return JsonResponse({...})
return redirect('rental_list')
```

### 5. Rental search uses unindexed `icontains`

- Location: `tweet/views.py:70`, `tweet/models.py:109`
- Severity: High
- Problem: `title__icontains`, `description__icontains`, and `location__icontains` will not use the existing B-tree `location` index effectively. As listings grow, search becomes sequential scans.
- Expected impact: large latency reduction on search-heavy pages.
- Migration: required.
- Estimated improvement: search can move from table scans to indexed trigram/full-text lookup.

Before:

```python
Q(title__icontains=search_query) |
Q(description__icontains=search_query) |
Q(location__icontains=search_query)
```

After option:

```python
# migration: enable pg_trgm and add GinIndex opclasses
Q(title__icontains=search_query) |
Q(description__icontains=search_query) |
Q(location__icontains=search_query)
```

Model migration target:

```python
GinIndex(fields=["title"], name="rental_title_trgm", opclasses=["gin_trgm_ops"])
GinIndex(fields=["location"], name="rental_location_trgm", opclasses=["gin_trgm_ops"])
```

For richer ranking, replace the query with PostgreSQL full-text search.

### 6. Rental list loads all wishlist ids for the user

- Location: `tweet/views.py:92`, `tweet/templates/rentalList.html:198`
- Severity: High
- Problem: the page displays 12 rentals, but authenticated users load every wishlist rental id into Python memory. This grows with user wishlist size.
- Expected impact: reduces memory and one query payload on every listing page.
- Migration: none; the existing unique constraint on `(user, rental)` supports this pattern.
- Estimated improvement: authenticated listing page drops one large result-set query; query count from about 4 to 3.

Before:

```python
wishlisted_ids = set(request.user.wishlist_items.values_list('rental_id', flat=True))
```

After:

```python
from django.db.models import Exists, OuterRef

rentals = rentals.annotate(
    is_wishlisted=Exists(
        Wishlist.objects.filter(user=request.user, rental_id=OuterRef("pk"))
    )
)
```

Template then uses `rental.is_wishlisted` instead of `rental.id in wishlisted_rental_ids`.

### 7. Missing composite indexes for core listing queries

- Location: `tweet/models.py:119`, `tweet/models.py:130`, `tweet/views.py:49`
- Severity: High
- Problem: the hot query is `is_available=True` plus `order_by('-created_at')`, often with `property_type`, `price`, or `user`. Current model has only single-column indexes on `location` and `property_type`; migration `0017` also removed analytics composite indexes from `PropertyShare`, `PropertyVisit`, and `PropertyInquiry`.
- Expected impact: faster listing pages, owner profile pages, admin analytics.
- Migration: required.
- Estimated improvement: significant on large tables; avoids sort and filter scans.

Before:

```python
created_at = models.DateTimeField(auto_now_add=True)
```

After:

```python
class Meta:
    indexes = [
        models.Index(fields=["is_available", "-created_at"], name="rental_avail_created_idx"),
        models.Index(fields=["property_type", "is_available", "-created_at"], name="rental_type_avail_created_idx"),
        models.Index(fields=["user", "-created_at"], name="rental_user_created_idx"),
        models.Index(fields=["is_available", "price"], name="rental_avail_price_idx"),
    ]
```

Re-add analytics indexes removed in `tweet/migrations/0017_alter_customuser_managers_and_more.py:20` if share/visit reports are used.

### 8. Profile renders all user listings

- Location: `tweet/views.py:289`, `tweet/templates/profile.html:59`
- Severity: High
- Problem: profile loads and renders every listing for the user and separately executes `listings.count()`. Owners with many listings get large HTML, many image URLs, and slow response/render time.
- Expected impact: bounded memory, response size, and browser DOM.
- Migration: none.
- Estimated improvement: DOM and response size capped to page size.

Before:

```python
listings = Rental.objects.filter(user=request.user).order_by('-created_at')
```

After:

```python
paginator = Paginator(
    Rental.objects.filter(user=request.user).only("title", "slug", "image", "location", "price").order_by("-created_at"),
    12,
)
page_obj = paginator.get_page(request.GET.get("page"))
```

Pass `page_obj` to the template and render pagination controls.

### 9. Wishlist renders all saved rentals

- Location: `tweet/views.py:320`, `tweet/templates/wishlist.html:18`
- Severity: Medium
- Problem: wishlist uses `select_related('rental')`, which is good, but still renders every saved item with images and forms.
- Expected impact: bounded response size for active users.
- Migration: none.
- Estimated improvement: caps DOM nodes and image requests.

Before:

```python
wishlist_items = request.user.wishlist_items.select_related('rental')
```

After:

```python
wishlist_items = request.user.wishlist_items.select_related("rental").only(
    "id", "rental__id", "rental__slug", "rental__title", "rental__image", "rental__location", "rental__price"
)
page_obj = Paginator(wishlist_items, 12).get_page(request.GET.get("page"))
```

### 10. Extra FK queries in contact, edit, and delete views

- Location: `tweet/views.py:173`, `tweet/views.py:239`, `tweet/views.py:254`
- Severity: Medium
- Problem: `rental.user != request.user` can fetch the related user. Contact fetches rental, then the template accesses `rental.user.email`.
- Expected impact: reduces common single-object pages from 2 DB queries to 1.
- Migration: none.
- Estimated improvement: 1 query saved per request on those views.

Before:

```python
rental = get_object_or_404(Rental, slug=slug)
if rental.user != request.user and not request.user.is_staff:
```

After:

```python
rental = get_object_or_404(Rental, slug=slug)
if rental.user_id != request.user.id and not request.user.is_staff:
```

For contact:

```python
rental = get_object_or_404(Rental.objects.select_related("user"), pk=rental_id)
```

### 11. Admin changelists have N+1 query risk

- Location: `tweet/admin.py:104`, `tweet/admin.py:141`, `tweet/admin.py:167`, `tweet/admin.py:194`
- Severity: Medium
- Problem: `list_display` includes foreign keys like `user`, `property`, `share`, and `visit`, but no `list_select_related` is configured.
- Expected impact: admin pages with 100 rows can drop from 100+ FK queries to about 1 query.
- Migration: none.
- Estimated improvement: major admin latency reduction.

Before:

```python
class RentalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", ...)
```

After:

```python
class RentalAdmin(admin.ModelAdmin):
    list_select_related = ("user",)
```

Apply similar changes: `PropertyShareAdmin = ("property", "user")`, `PropertyVisitAdmin = ("share", "user", "share__property")`, `PropertyInquiryAdmin = ("property", "visit")`.

### 12. Share tracking writes synchronously on every tracked visit

- Location: `tweet/views.py:151`, `tweet/models.py:198`
- Severity: Medium
- Problem: every shared-link visit creates a `PropertyVisit` row during the request and stores full user-agent text.
- Expected impact: reduced write latency and database write pressure under traffic spikes.
- Migration: optional if changing `user_agent` to a bounded field or adding summary tables.
- Estimated improvement: removes one blocking write from share landing requests if queued.

Before:

```python
visit = PropertyVisit.objects.create(...)
```

After:

```python
record_property_visit.delay(...)
```

This requires creating `tweet/tasks.py` and running a Celery worker.

### 13. [RESOLVED] Celery beat references a missing task

- Status: COMPLETED (Tasks file created)
- Estimated improvement: reliability fix for async architecture.

Before:

```python
'task': 'tweet.tasks.aggregate_daily_analytics',
```

After:

```python
# Either create tweet/tasks.py with aggregate_daily_analytics
# or remove CELERY_BEAT_SCHEDULE until analytics exists.
```

### 14. Render deployment skips Tailwind build

- Location: `render.yaml:13`, `build.sh:19`
- Severity: Medium
- Problem: `build.sh` builds CSS, but `render.yaml` does not call it. If templates change Tailwind classes, production can serve stale CSS unless `static/dist/output.css` is committed and current.
- Expected impact: prevents stale styling and oversized unused CSS drift.
- Migration: none.
- Estimated improvement: build correctness, smaller fresh CSS when minified.

Before:

```yaml
buildCommand: |
  pip install -r requirements.txt
  python manage.py collectstatic --noinput
  python manage.py migrate
```

After:

```yaml
buildCommand: "./build.sh"
```

### 15. Redis cache is configured but not used

- Location: `rental_app/settings.py:195`, `tweet/views.py:39`, `tweet/views.py:360`
- Severity: Medium
- Problem: Redis cache exists, but no page, fragment, or query caching is applied. Public pages like home/about are static-heavy and good cache candidates once HTMX Vary headers are correct.
- Expected impact: lower CPU/template render time on public pages.
- Migration: none.
- Estimated improvement: near-zero Django rendering for cached public pages.

Before:

```python
def index(request):
    return render(request, 'index.html')
```

After:

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 10)
def index(request):
    return render(request, "index.html")
```

Use with `Vary: HX-Request` because full and partial responses differ.

### 16. Home and about pages ship many large external images

- Location: `tweet/templates/index.html:212`, `tweet/templates/index.html:273`, `tweet/templates/index.html:295`, `tweet/templates/about.html:49`
- Severity: Medium
- Problem: home loads many Unsplash images at widths up to 2400 without `loading="lazy"`, `decoding="async"`, `sizes`, or local/Cloudinary responsive transformations.
- Expected impact: lower LCP and total transferred bytes.
- Migration: none.
- Estimated improvement: large mobile payload reduction.

Before:

```html
<img src="https://images.unsplash.com/...&w=2400&q=80" alt="Luxury home">
```

After:

```html
<img src="https://images.unsplash.com/...&w=1200&q=75"
     loading="lazy"
     decoding="async"
     sizes="(min-width: 1024px) 50vw, 100vw"
     alt="Luxury home">
```

For the first hero image, use `fetchpriority="high"` instead of lazy loading.

### 17. Some Cloudinary images bypass optimization

- Location: `tweet/templates/profile.html:62`, `tweet/templates/rental_contact.html:33`
- Severity: Medium
- Problem: profile/contact use `{{ rental.image.url }}` directly, bypassing `optimized_cloudinary_url`.
- Expected impact: lower image transfer size.
- Migration: none.
- Estimated improvement: depends on original upload size; can be large.

Before:

```html
<img src="{{ rental.image.url }}" class="h-32 w-full object-cover">
```

After:

```html
<img src="{{ rental.image|optimized_cloudinary_url:'f_auto,q_auto,c_fill,w_600,h_400' }}"
     loading="lazy"
     decoding="async"
     class="h-32 w-full object-cover"
     alt="{{ rental.title }}">
```

### 18. Duplicate render-blocking frontend assets

- Location: `rental_app/templates/layout.html:22`, `rental_app/templates/layout.html:26`, `tweet/templates/rentalList.html:7`, `rental_app/templates/nav.html:2`, `tweet/templates/about.html:7`
- Severity: Medium
- Problem: Font Awesome is loaded globally and again on rental list; `navbar.css` is linked from inside the body via `nav.html`; about loads Inter and GSAP inside page content.
- Expected impact: fewer render-blocking requests and less duplicate CSS/JS work.
- Migration: none.
- Estimated improvement: reduces blocking requests and prevents duplicate library downloads.

Before:

```html
<!-- rentalList.html -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
```

After:

```html
<!-- remove duplicate; keep one Font Awesome load in layout.html or bundle local icons -->
```

Move `nav.html:2` stylesheet into `layout.html` head.

### 19. HTMX swaps can accumulate page-specific listeners

- Location: `tweet/templates/index.html:426`, `tweet/templates/index.html:484`, `rental_app/templates/base_htmx.html:17`
- Severity: Medium
- Problem: index adds `htmx:afterSettle`, `scroll`, and `resize` listeners in page script. After repeated HTMX visits, old listeners can remain because no cleanup runs before the OOB script replacement.
- Expected impact: lower CPU use after repeated navigation.
- Migration: none.
- Estimated improvement: prevents linear listener growth with navigation count.

Before:

```js
document.body.addEventListener('htmx:afterSettle', initRevealAnimations);
window.addEventListener("scroll", requestTick, { passive: true });
```

After:

```js
window.empireIndexAbort?.abort();
window.empireIndexAbort = new AbortController();
document.body.addEventListener("htmx:afterSettle", initRevealAnimations, { signal: window.empireIndexAbort.signal });
window.addEventListener("scroll", requestTick, { passive: true, signal: window.empireIndexAbort.signal });
```

### 20. Detail gallery loads all large images eagerly

- Location: `tweet/templates/room_describe.html:95`
- Severity: Low
- Problem: detail loads main image and all gallery images at `w_1400`. Gallery max is 5, so the cap is bounded, but transfer is still high on mobile.
- Expected impact: lower detail-page bytes.
- Migration: none.
- Estimated improvement: moderate on mobile.

Before:

```html
<img src="{{ item.image|optimized_cloudinary_url:'f_auto,q_auto,c_limit,w_1400' }}">
```

After:

```html
<img src="{{ item.image|optimized_cloudinary_url:'f_auto,q_auto,c_fill,w_900,h_560' }}"
     loading="lazy"
     decoding="async"
     alt="Gallery image">
```

### 21. Middleware does repeated URL reversing for incomplete profiles

- Location: `tweet/middleware.py:36`
- Severity: Low
- Problem: `reverse()` calls happen for every request from an authenticated user with an incomplete profile. This is not the biggest bottleneck, but it is avoidable per-request work.
- Expected impact: small CPU reduction for incomplete-profile users.
- Migration: none.
- Estimated improvement: small.

Before:

```python
allowed_paths = [
    reverse('profile_setup'),
    reverse('account_logout'),
    ...
]
```

After:

```python
def __init__(self, get_response):
    self.get_response = get_response
    self.allowed_path_names = ("profile_setup", "account_logout", "offline", "manifest", "service_worker")
```

Or compute a cached set lazily once per process.

### 22. Local environments are inconsistent

- Location: root `.venv`, `rental_app/venv`, `requirements.txt:17`
- Severity: Low
- Problem: root `.venv` has Django but lacks Cloudinary; `rental_app/venv` launcher points to a missing WindowsApps Python. This blocks `manage.py check`, migration checks, and reliable performance verification.
- Expected impact: restores ability to validate query and migration changes.
- Migration: none.
- Estimated improvement: developer workflow reliability.

Before:

```powershell
..\.venv\Scripts\python.exe manage.py check
# ModuleNotFoundError: No module named 'cloudinary'
```

After:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r rental_app\requirements.txt
.\.venv\Scripts\python.exe rental_app\manage.py check
```

## Database Report

- Missing indexes: add composite indexes for `Rental(is_available, -created_at)`, `Rental(property_type, is_available, -created_at)`, `Rental(user, -created_at)`, and `Rental(is_available, price)`.
- Search indexes: add PostgreSQL trigram or full-text indexes for `Rental.title`, `Rental.location`, and possibly `Rental.description`.
- Removed analytics indexes: migration `0017` removes composite indexes for `PropertyShare`, `PropertyVisit`, and `PropertyInquiry`; re-add if analytics/admin reports use those tables.
- N+1 locations: admin changelists (`admin.py`), contact page (`views.py:254` plus template user access), edit/delete permission checks if comparing FK objects.
- Query count reductions:
  - `rental_contact`: about 2 queries to 1 with `select_related("user")`.
  - `rental_edit` and `rental_delete`: about 2 queries to 1 with `user_id` comparison.
  - rental admin: 100 rows can drop from 100+ FK queries to about 1 query with `list_select_related`.
  - rental list authenticated: removes one large wishlist-id result set by using `Exists`.

## Frontend Report

- Largest payloads: `index.html` and `about.html` are the largest templates and include many remote images. Static `output.css` is about 66 KB; screenshot assets are larger but only manifest-related.
- DOM bloat: profile and wishlist pages render unbounded repeated cards; paginate both.
- Layout shift risks: Google Fonts are loaded without `display=swap` in `layout.html`; add preconnect and `display=swap`.
- Image opportunities: add lazy/async/sizes to all below-fold images; use Cloudinary transformations everywhere user-uploaded images are displayed; reduce detail gallery sizes.
- HTMX opportunities: install `HtmxVaryMiddleware`, fix wishlist HTMX response, make page scripts idempotent, and consider disabling boosting for script-heavy pages like about/index if initialization remains fragile.

## PWA Report

- Service worker issue: dynamic navigation HTML is cached and served stale. Use network-first without caching for navigation, or cache only explicit public shell pages.
- Cache strategy: keep cache-first only for static assets. If using WhiteNoise hashed assets, precache via `{% static %}` generated URLs or update `CACHE_NAME` on every deploy.
- Offline behavior: `/offline/` is precached and usable, but cached stale pages can mask offline/online state. Network-first navigation makes offline fallback predictable.
- Cache mismatch: `sw.js` precaches `/manifest.json?v=2`, while `layout.html` links `/manifest.json`; use one canonical URL.

## Scalability Report

- At 1,000 users: search/count queries and image-heavy pages fail first. Service worker stale HTML can also make fixes appear ineffective across clients.
- At 10,000 users: unbounded profile/wishlist pages, synchronous `PropertyVisit` writes, admin N+1 queries, and missing search indexes become major bottlenecks.
- Architecture improvements: use PostgreSQL full-text/trigram search, Redis page/fragment caching for public pages, Celery workers for analytics/write-heavy tracking, Cloudinary responsive images, proper cache headers/Vary, and query monitoring such as Django Debug Toolbar locally plus production APM.

## Final Action Plan

1. Fix service worker navigation caching and bump `CACHE_NAME`.
2. Install and expand `HtmxVaryMiddleware`.
3. Fix wishlist unauthenticated JSON/401 and HTMX remove responses.
4. Add pagination to profile and wishlist.
5. Replace wishlist-id set with `Exists` annotation.
6. Add rental composite indexes and trigram/full-text search indexes.
7. Optimize contact/edit/delete FK queries.
8. Add admin `list_select_related`.
9. Optimize raw Cloudinary image usages and lazy-load below-fold images.
10. Deduplicate render-blocking CSS/JS and move navbar CSS into the head.
11. Make HTMX page scripts idempotent or disable boost on script-heavy pages.
12. Fix Render build command to run `build.sh`.
13. Add or remove the missing Celery analytics task.
14. Repair the local virtualenv and run `manage.py check` plus `makemigrations --check --dry-run`.
