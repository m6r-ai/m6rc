/*
 * heap_get_free()
 *	Return the amount of heap space that's still available.
 */
addr_t heap_get_free(void)
{
	addr_t ret;
	
	spinlock_lock(&heap_lock);
	ret = free_ram;
	spinlock_unlock(&heap_lock);

	return ret;
}

