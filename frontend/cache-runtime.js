(function attachSPMSCacheRuntime(globalObject) {
  const DEFAULT_MAX_AGE_MS = 15 * 60 * 1000;

  function getStorage() {
    if (typeof window === "undefined") {
      return null;
    }
    if (window.localStorage) {
      return window.localStorage;
    }
    if (window.sessionStorage) {
      return window.sessionStorage;
    }
    return null;
  }

  function readEnvelope(storageKey, { identity = "", maxAgeMs = DEFAULT_MAX_AGE_MS, allowStale = false } = {}) {
    const storage = getStorage();
    if (!storage) {
      return null;
    }
    try {
      const raw = storage.getItem(storageKey);
      if (!raw) {
        return null;
      }
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        return null;
      }
      if (identity && String(parsed.identity || "") !== String(identity)) {
        return null;
      }
      if (!allowStale) {
        const cachedAt = Number(parsed.cached_at || 0);
        if (!Number.isFinite(cachedAt) || cachedAt <= 0 || (Date.now() - cachedAt) > maxAgeMs) {
          return null;
        }
      }
      return parsed;
    } catch (_error) {
      return null;
    }
  }

  function writeEnvelope(storageKey, { identity = "", payload = {}, cachedAt = Date.now() } = {}) {
    const storage = getStorage();
    if (!storage) {
      return false;
    }
    try {
      storage.setItem(
        storageKey,
        JSON.stringify({
          identity: String(identity || ""),
          cached_at: Number(cachedAt || Date.now()) || Date.now(),
          payload,
        }),
      );
      return true;
    } catch (_error) {
      return false;
    }
  }

  globalObject.SPMSCacheRuntime = {
    DEFAULT_MAX_AGE_MS,
    getStorage,
    readEnvelope,
    writeEnvelope,
  };
})(window);
