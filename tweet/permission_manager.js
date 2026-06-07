/**
 * PermissionManager handles browser hardware APIs and coordinates with Django.
 */
const PermissionManager = {
    debugEnv: () => {
        console.log("--- Permission Debug ---");
        console.log("Secure Context (HTTPS/Localhost):", window.isSecureContext);
        console.log("MediaDevices Support:", !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia));
        if (!window.isSecureContext) {
            console.error("CRITICAL: Camera access requires HTTPS or localhost.");
        }
    },

    // Request logic for different types
    strategies: {
        camera: async () => {
            PermissionManager.debugEnv();
            try {
                if (!navigator.mediaDevices) throw new Error("MediaDevices not supported");
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                stream.getTracks().forEach(track => track.stop()); // Close immediately after check
                console.log("Camera access granted.");
                return 'granted';
            } catch (e) {
                console.error("Camera access error:", e);
                return 'denied';
            }
        },
        files: async () => {
            // Browser file access is usually implicit on input click, 
            // but we use this to verify the environment supports it.
            return 'granted'; 
        }
    },

    async check(permissionType) {
        if (navigator.permissions && navigator.permissions.query) {
            try {
                const status = await navigator.permissions.query({ name: permissionType === 'camera' ? 'camera' : 'notifications' });
                return status.state;
            } catch (e) {
                console.warn("Permissions API query failed.");
            }
        }
        return localStorage.getItem(`perm_${permissionType}`) || 'prompt';
    },

    async request(permissionType) {
        if (this.strategies[permissionType]) {
            const result = await this.strategies[permissionType]();
            localStorage.setItem(`perm_${permissionType}`, result);
            return result;
        }
        return 'denied';
    },

    getVerifiedHeader(requiredList) {
        // Returns a string of permissions that the frontend is vouching for
        return requiredList.join(',');
    },

    async handleManualClick(target, permissions) {
        const checkPromises = permissions.map(p => this.check(p));
        const statuses = await Promise.all(checkPromises);

        if (statuses.some(s => s !== 'granted')) {
            showPermissionModal(permissions, async () => {
                const results = await Promise.all(
                    permissions.map(p => this.request(p))
                );

                if (results.every(r => r === 'granted')) {
                    hidePermissionModal();
                    target.click(); // Re-trigger the click now that we have permission
                } else {
                    alert("Permission denied. We cannot proceed without hardware access.");
                }
            });
        }
    }
};

// Proactive HTMX Integration: Intercept BEFORE the request is sent
document.body.addEventListener('htmx:confirm', async (evt) => {
    const elt = evt.detail.elt;
    // Look for data-require-perms attribute (e.g., data-require-perms="camera")
    const requiredPermsAttr = elt.getAttribute('data-require-perms');
    
    if (requiredPermsAttr) {
        const permissions = requiredPermsAttr.split(',').map(p => p.trim());
        
        // Check if any permission is not yet 'granted'
        const checkPromises = permissions.map(p => PermissionManager.check(p));
        const statuses = await Promise.all(checkPromises);

        if (statuses.some(s => s !== 'granted')) {
            // Halt the HTMX request
            evt.preventDefault();
            
            showPermissionModal(permissions, async () => {
                // Request native browser permissions
                const results = await Promise.all(
                    permissions.map(p => PermissionManager.request(p))
                );

                if (results.every(r => r === 'granted')) {
                    hidePermissionModal();
                    // Manually trigger the original HTMX action
                    evt.detail.issueRequest();
                } else {
                    alert("Permission denied. We cannot proceed without hardware access.");
                }
            });
        }
    }
});

// Add support for clicking standard file inputs or "Add Photo" buttons
document.body.addEventListener('click', async (evt) => {
    const elt = evt.target.closest('[data-require-perms]');
    if (!elt) return;

    // If it's a file input and we don't have permissions yet, intercept the click
    if (elt.tagName === 'INPUT' && elt.type === 'file' && !elt.dataset.permVerified) {
        const permissions = elt.getAttribute('data-require-perms').split(',').map(p => p.trim());
        evt.preventDefault();
        await PermissionManager.handleManualClick(elt, permissions);
        elt.dataset.permVerified = "true";
    }
});

function showPermissionModal(perms, onConfirm) {
    const modal = document.getElementById('permission-modal');
    const list = document.getElementById('permission-list');
    if (!modal) return;

    list.innerHTML = perms.map(p => `
        <div class="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10">
            <i class="fa-solid fa-${p === 'camera' ? 'camera' : 'file-import'} text-sky-400"></i>
            <span class="capitalize text-sm font-bold">${p} Access</span>
        </div>
    `).join('');

    modal.classList.remove('hidden');
    document.getElementById('confirm-permission-btn').onclick = onConfirm;
}

function hidePermissionModal() {
    const modal = document.getElementById('permission-modal');
    if (modal) modal.classList.add('hidden');
}