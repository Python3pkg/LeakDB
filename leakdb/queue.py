# -*- coding: utf-8 -*-

from datetime import datetime

from gevent import spawn, sleep as g_sleep
from gevent.queue import JoinableQueue, Empty

from leakdb import logger


class LeakQueue(object):

    def __init__(self, maxsize=0, workers=10):
        """ Setup the gevent queue and the workers.

        :param int maxsize: the max lenght of the queue, default the queue size is infinite.
        :param int workers: the number of workers, default=10.
        """
        self.queue = JoinableQueue(maxsize=maxsize)
        [spawn(self.worker) for x in range(workers)]

    def __repr__(self):
        return '{} items in queue'.format(self.queue.qsize())

    def put(self, operation, item, date=None):
        """ Each item are queued for a later processing.

        :param str operation: the operation name.
        :param item: the item to queued.
        :param date date: when the item is trigger.

        :returns: True if insertions succeeds, False otherwise.
        """
        try:
            self.queue.put({"operation": operation, "item": item, "date": date or datetime.utcnow()})
            self.flush()
        except Exception as e:
            logger.critical('unable to put an item in the queue :: {}'.format(e))
            return False
        else:
            return True

    def flush(self, force=False):
        """ Flush the queue and block until all tasks are done.

        :param boolean force: force the queue flushing

        :returns: True if the flush occurs, False otherwise.
        """
        if self.queue.full() or force:
            logger.info('queue is full ({} items) :: flush it !'.format(self.queue.qsize()))
            self.queue.join()
            return True
        return False

    def worker(self):
        while True:
            try:
                item = self.queue.get()
                logger.info('get item :: {}'.format(item))

                if not self.worker_process(item):
                    logger.info('re-queue item :: {}'.format(item))
                    self.queue.put(item)
            except Empty:
                logger.info('queue is empty')
            else:
                self.queue.task_done()

    def worker_process(self, item):
        """ Default action execute by each worker.
            Must return a True statement to remove the item,
            otherwise the worker put the item into the queue.
        """
        g_sleep()
        return item
