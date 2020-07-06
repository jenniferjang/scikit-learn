"""Subsampled neighbors transformer"""

# Author: Jennifer Jang <j.jang42@gmail.com>
#         Heinrich Jiang <heinrichj@google.com>
#
# License: BSD 3 clause

import numpy as np

from ..metrics.pairwise import paired_distances, check_pairwise_arrays, \
    PAIRED_DISTANCES
from ._base import UnsupervisedMixin
from ..base import TransformerMixin, BaseEstimator
from ..utils import check_random_state
from ..utils.validation import check_is_fitted, _deprecate_positional_args
from ..utils.validation import check_array


class SubsampledNeighborsTransformer(TransformerMixin, UnsupervisedMixin,
                                     BaseEstimator):
    """Compute subsampled sparse distance matrix of neighboring points in X.

    Parameters
    ----------

    s : float
        Sampling probability.

    eps : float, default=None
        Neighborhood radius. Pairs of points which are at most eps apart are
        considered neighbors. If None, radius is assumed to be infinity.

    metric : string or callable, default='euclidean'
        Input to paired_distances function. Can be string specified
        in PAIRED_DISTANCES, including "euclidean", "manhattan", or
        "cosine." Alternatively, can be a callable function, which should
        take two arrays from X as input and return a value indicating
        the distance between them.

    random_state : int, RandomState instance, default=None
        Seeds the random sampling of lists of vertices. Use an int to 
        make the randomness deterministic.
        See :term:`Glossary <random_state>`.

    Attributes
    ----------
    random_state_ : numpy.RandomState
        Pseudo random number generator object used during initialization.

    References
    ----------
    - Faster DBSCAN via subsampled similarity queries, 2020
        Heinrich Jiang, Jennifer Jang, Jakub Łącki
        https://arxiv.org/abs/2006.06743

    Notes
    -----
    Each pair of points in X is sampled uniformly with probability s,
    and the final distance matrix is symmetric.
    """

    @_deprecate_positional_args
    def __init__(self, s=0.1, eps=None, *, metric='euclidean', random_state=None):
        self.s = s
        self.eps = eps
        self.metric = metric
        self.random_state = random_state
        self._check_algorithm_metric()

    def _check_algorithm_metric(self):
        if self.s < 0:
            raise ValueError("Sampling rate needs to be non-negative: %s" % 
                self.s)

        if self.eps is not None and self.eps <= 0:
            raise ValueError("Epsilon needs to be positive: %s" % self.eps)

        if self.metric not in PAIRED_DISTANCES and not callable(self.metric):
            raise ValueError('Unknown distance %s' % self.metric)

    def _fit(self, X):
        self._fit_X = check_array(X, accept_sparse='csr')
        self.random_state_ = check_random_state(self.random_state)

        return self

    def transform(self, X):
        """Transform data into a subsampled graph of neighbors.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Sample data.

        Returns
        -------
        neighborhood : sparse matrix of shape (n_samples, n_samples)
            Sparse matrix where the i-jth value is equal to the distance 
            between X[i] and X[j] for randomly sampled pairs of neighbors.
            The matrix is of CSR format.
        """

        check_is_fitted(self)

        return self.subsampled_neighbors(X, self.s, self.eps, self.metric,
            self.random_state_)

    def fit_transform(self, X, y=None):
        """Fit to data, then transform it.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Sample data.
        y : ignored

        Returns
        -------
        neighborhood : sparse matrix of shape (n_samples, n_samples)
            Sparse matrix where the i-jth value is equal to the distance 
            between X[i] and X[j] for randomly sampled pairs of neighbors.
            The matrix is of CSR format.
        """
        
        return self.fit(X).transform(X)

    def subsampled_neighbors(self, X, s, eps=None, metric='euclidean', 
                             random_state=None):
        """Compute the subsampled sparse distance matrix of neighboring 
        points in X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Sample data.

        s : float
            Sampling probability.

        eps : float, default=None
            Neighborhood radius. Pairs of points which are at most eps apart 
            are considered neighbors. If not given, radius is assumed to be 
            infinity.

        metric : string or callable, default='euclidean'
            Input to paired_distances function. Can be string specified 
            in PAIRED_DISTANCES, including "euclidean", "manhattan", or 
            "cosine." Alternatively, can be a callable function, which should 
            take two arrays from X as input and return a value indicating 
            the distance between them.

        random_state : int, RandomState instance, default=None
            Seeds the random sampling of lists of vertices. Use an int to 
            make the randomness deterministic.
            See :term:`Glossary <random_state>`.

        Returns
        -------
        neighborhood : sparse matrix of shape (n_samples, n_samples)
            Sparse matrix where the i-jth value is equal to the distance 
            between X[i] and X[j] for randomly sampled pairs of neighbors.
            The matrix is of CSR format.
        """

        from scipy.sparse import csr_matrix

        X = check_pairwise_arrays(X, self._fit_X, accept_sparse='csr')[0]

        n_samples = X.shape[0]

        # We use sampling rate s/2 because each edge has two chances of being 
        # sampled: as (i, j) and (j, i)
        n_edges = int(n_samples * n_samples * s / 2)

        # No edges sampled
        if n_edges < 1:
          return csr_matrix((n_samples, n_samples), dtype=np.float)

        # Sample the edges with replacement
        x = random_state.choice(n_samples, size=n_edges, replace=True)
        y = random_state.choice(n_samples, size=n_edges, replace=True)

        # Remove duplicates
        neighbors = np.block([[x, y], [y, x]])
        neighbors = neighbors[:, neighbors[0] > neighbors[1]]
        neighbors = np.unique(neighbors, axis=1)

        distances = paired_distances(X[neighbors[0]], X[neighbors[1]], 
            metric=metric)

        if eps is not None:
          neighbors = neighbors[:, distances <= eps]
          distances = distances[distances <= eps]

        neighborhood = csr_matrix((distances, neighbors), 
            shape=(n_samples, n_samples), dtype=np.float)

        # Make the matrix symmetric
        neighborhood += neighborhood.transpose()

        return neighborhood
