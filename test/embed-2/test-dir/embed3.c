/*
 * heap_dump_stats()
 */
int heap_dump_stats(struct memory_hole *mbuf, int max)
{
	struct memory_hole *mh;
        int ct = 0;
		
	spinlock_lock(&heap_lock);

	mh = first_hole;
	while (mh && (ct < max)) {
		mbuf->mh_next = mh;
		mbuf->mh_size = mh->mh_size;
		mbuf++;
		ct++;
		mh = mh->mh_next;
	}
	
	spinlock_unlock(&heap_lock);

	return ct;
}

