(function attachAdminGoogleSheetsCacheRuntime(global) {
  var STORAGE_KEY = "notice-winner-pipeline-web.adminGoogleSheetsCache.v1";

  function isPlainObject(value) {
    if (!value || typeof value !== "object") {
      return false;
    }
    if (Array.isArray(value)) {
      return false;
    }
    return Object.prototype.toString.call(value) === "[object Object]";
  }

  function getStorage(options) {
    var next = options || {};
    if (next.storage) {
      return next.storage;
    }
    if (global && global.window && global.window.localStorage) {
      return global.window.localStorage;
    }
    if (global && global.localStorage) {
      return global.localStorage;
    }
    return null;
  }

  function readStoredEnvelope(storage) {
    if (!storage || typeof storage.getItem !== "function") {
      return null;
    }
    try {
      var rawValue = storage.getItem(STORAGE_KEY);
      if (!rawValue) {
        return null;
      }
      return JSON.parse(rawValue);
    } catch (error) {
      return null;
    }
  }

  function isValidBootstrap(bootstrap) {
    if (!isPlainObject(bootstrap)) {
      return false;
    }
    if (Array.isArray(bootstrap.tabs)) {
      return true;
    }
    if (!isPlainObject(bootstrap.tabs)) {
      return false;
    }
    for (var key in bootstrap.tabs) {
      if (Object.prototype.hasOwnProperty.call(bootstrap.tabs, key) && !isPlainObject(bootstrap.tabs[key])) {
        return false;
      }
    }
    return true;
  }

  function isValidPayload(payload) {
    if (!isPlainObject(payload)) {
      return false;
    }
    var hasLegacyShape = Array.isArray(payload.header_cells) && Array.isArray(payload.row_cells);
    var hasNewShape = Array.isArray(payload.headers) && Array.isArray(payload.rows);
    return hasLegacyShape || hasNewShape;
  }

  function normalizePayload(payload) {
    if (Array.isArray(payload.header_cells) && Array.isArray(payload.row_cells)) {
      return {
        key: payload.key,
        header_cells: payload.header_cells,
        row_cells: payload.row_cells,
      };
    }
    return {
      key: payload.key,
      headers: payload.headers,
      rows: payload.rows,
    };
  }

  function readAdminGoogleSheetsCache(options) {
    try {
      var storage = getStorage(options);
      var envelope = readStoredEnvelope(storage);
      if (!isPlainObject(envelope)) {
        return null;
      }

      var savedAt = envelope.saved_at;
      var bootstrap = envelope.bootstrap;
      var payloadsByKey = envelope.payloads_by_key;
      if (!Number.isFinite(savedAt) || !isValidBootstrap(bootstrap) || !isPlainObject(payloadsByKey)) {
        return null;
      }

      var resultPayloads = {};
      for (var key in payloadsByKey) {
        if (Object.prototype.hasOwnProperty.call(payloadsByKey, key)) {
          var payload = payloadsByKey[key];
          if (!isValidPayload(payload)) {
            return null;
          }
          resultPayloads[key] = normalizePayload(payload);
        }
      }

      return {
        savedAt: savedAt,
        bootstrap: bootstrap,
        payloadsByKey: resultPayloads,
      };
    } catch (error) {
      return null;
    }
  }

  function writeAdminGoogleSheetsCache(value, options) {
    try {
      var storage = getStorage(options);
      if (!storage || typeof storage.setItem !== "function") {
        return false;
      }

      var bootstrap = value && value.bootstrap;
      var payloadsByKey = value && value.payloadsByKey;
      if (!isValidBootstrap(bootstrap) || !isPlainObject(payloadsByKey)) {
        return false;
      }

      var normalizedPayloads = {};
      for (var key in payloadsByKey) {
        if (Object.prototype.hasOwnProperty.call(payloadsByKey, key)) {
          var payload = payloadsByKey[key];
          if (!isValidPayload(payload)) {
            return false;
          }
          normalizedPayloads[key] = normalizePayload(payload);
        }
      }

      storage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          saved_at: Number((options && typeof options.nowFn === "function" ? options.nowFn() : Date.now())) || 0,
          bootstrap: bootstrap,
          payloads_by_key: normalizedPayloads,
        }),
      );
      return true;
    } catch (error) {
      return false;
    }
  }

  function clearAdminGoogleSheetsCache(options) {
    try {
      var storage = getStorage(options);
      if (!storage || typeof storage.removeItem !== "function") {
        return false;
      }
      storage.removeItem(STORAGE_KEY);
      return true;
    } catch (error) {
      return false;
    }
  }

  global.SPMSAdminGoogleSheetsCacheRuntime = {
    STORAGE_KEY: STORAGE_KEY,
    clearAdminGoogleSheetsCache: clearAdminGoogleSheetsCache,
    getStorage: getStorage,
    readAdminGoogleSheetsCache: readAdminGoogleSheetsCache,
    writeAdminGoogleSheetsCache: writeAdminGoogleSheetsCache,
  };
})(window);
