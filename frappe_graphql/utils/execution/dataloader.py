class DataLoader:
    class LazyValue:
        def __init__(self, key, dataloader):
            self.key = key
            self.dataloader = dataloader

        def get(self):
            return self.dataloader.get(self.key)

    def __init__(self, load_fn):
        self.load_fn = load_fn
        self.pending_ids = set()
        self.loaded_ids = {}

    def load(self, key):
        lazy_value = DataLoader.LazyValue(key, self)
        self.pending_ids.add(key)

        return lazy_value

    def get(self, key):
        if key in self.loaded_ids:
            return self.loaded_ids.get(key)

        keys = self.pending_ids
        values = self.load_fn(keys)
        for k, value in zip(keys, values):
            self.loaded_ids[k] = value

        self.pending_ids.clear()
        return self.loaded_ids[key]
