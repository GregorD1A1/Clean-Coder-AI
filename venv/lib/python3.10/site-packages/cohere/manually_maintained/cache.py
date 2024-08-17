import typing
import time


class CacheMixin:
    # A simple in-memory cache with TTL (thread safe). This is used to cache tokenizers at the moment.
    _cache: typing.Dict[str, typing.Tuple[typing.Optional[float], typing.Any]] = dict()

    def _cache_get(self, key: str) -> typing.Any:
        val = self._cache.get(key)
        if val is None:
            return None
        expiry_timestamp, value = val
        if expiry_timestamp is None or expiry_timestamp > time.time():
            return value

        del self._cache[key]  # remove expired cache entry

    def _cache_set(self, key: str, value: typing.Any, ttl: int = 60 * 60) -> None:
        expiry_timestamp = None
        if ttl is not None:
            expiry_timestamp = time.time() + ttl
        self._cache[key] = (expiry_timestamp, value)
