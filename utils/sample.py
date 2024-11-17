import numpy as np
from numpy.random import default_rng # type: ignore
# from six import with_metaclass
from meta import ParamBase


class Patch(ParamBase):
        
    @staticmethod
    def on_align(downsamples, snapshot):
        """
            align ohlcv by snapshot 
        """
        downsamples[0] = snapshot[0]
        downsamples[-1] = snapshot[-1]
        max_idx = np.argmax(downsamples)
        downsamples[max_idx] = np.max(snapshot)
        min_idx = np.argmin(downsamples)
        downsamples[min_idx] = np.min(snapshot)
        return downsamples
    
    def patch(self, datas):
        raise NotImplementedError("240/m minute to 4800 3/s tick")
    

class BetaPatch(Patch):
    """
        level1  stock  3/s
        level1  future 250/ms
    """

    params = (
        ("alias", "beta"),
        ("size", 20),
        ("prior", {"a":1, "b": 2})
    )

    def prob_infer(self):
        rng = default_rng()
        probs = rng.beta(a=self.p.prior["a"], b=self.p.prior["b"], size=self.p.size)
        return probs

    def on_patch(self, snapshot):
        """
            snapshot: np.array[t-1,t]
            beta distribution
        """
        aggerated_vol = snapshot[-1]["volume"]
        delta = np.max(snapshot[:, -1]) - np.min(snapshot[:, -1])
        probs = self.prob_infer(snapshot)
        # ohlc
        tick_prices = delta * np.array(probs) + np.min(snapshot)
        align_tick_prices = self.on_align(tick_prices, snapshot=snapshot)
        # volume
        ratio = np.array(probs) / np.sum(probs)
        tick_vols = aggerated_vol * ratio
        return align_tick_prices, tick_vols


class LinearPatch(BetaPatch):

    params = (("size", 20),)

    def patch_infer(self):
        """
            linear sample
        """
        probs = range(1, self.p.size+1) / self.p.size
        return probs
