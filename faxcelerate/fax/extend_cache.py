# Lazy support

from django.core.cache import cache

def lazy_get(key, *args, **kwargs):
	c = cache.get(key)
	if c is not None:
		return c
	try:
		f = args[0]
		if callable(f):
			f = f()
		return cache.get(key, f, *args[1:], **kwargs)
	except IndexError:
		return None

cache.lazy_get = lazy_get