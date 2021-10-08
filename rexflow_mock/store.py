
class Store:
    tasks = {}

    @classmethod
    def save_task(cls, xid, iid, tid):
        cls.tasks[xid] = {
            'iid': iid,
            'tid': tid,
        }

    @classmethod
    def get_task(cls, xid):
        return cls.tasks.get(xid)
