"""Nearest Neighbors graph functions"""

# Author: Jake Vanderplas <vanderplas@astro.washington.edu>
#
# License: BSD 3 clause (C) INRIA, University of Amsterdam
import numpy as np

from .base import KNeighborsMixin, RadiusNeighborsMixin
from .base import NeighborsBase
from .base import UnsupervisedMixin
from .unsupervised import NearestNeighbors
from ..base import TransformerMixin
from ..utils.validation import check_is_fitted, check_array


def _check_params(X, metric, p, metric_params):
    """Check the validity of the input parameters"""
    params = zip(['metric', 'p', 'metric_params'],
                 [metric, p, metric_params])
    est_params = X.get_params()
    for param_name, func_param in params:
        if func_param != est_params[param_name]:
            raise ValueError(
                "Got %s for %s, while the estimator has %s for "
                "the same parameter." % (
                    func_param, param_name, est_params[param_name]))


def _query_include_self(X, include_self):
    """Return the query based on include_self param"""
    if include_self:
        query = X._fit_X
    else:
        query = None

    return query


def kneighbors_graph(X, n_neighbors, mode='connectivity', metric='minkowski',
                     p=2, metric_params=None, include_self=False, n_jobs=1):
    """Computes the (weighted) graph of k-Neighbors for points in X

    Read more in the :ref:`User Guide <unsupervised_neighbors>`.

    Parameters
    ----------
    X : array-like or BallTree, shape = [n_samples, n_features]
        Sample data, in the form of a numpy array or a precomputed
        :class:`BallTree`.

    n_neighbors : int
        Number of neighbors for each sample.

    mode : {'connectivity', 'distance'}, optional
        Type of returned matrix: 'connectivity' will return the connectivity
        matrix with ones and zeros, and 'distance' will return the distances
        between neighbors according to the given metric.

    metric : string, default 'minkowski'
        The distance metric used to calculate the k-Neighbors for each sample
        point. The DistanceMetric class gives a list of available metrics.
        The default distance is 'euclidean' ('minkowski' metric with the p
        param equal to 2.)

    p : int, default 2
        Power parameter for the Minkowski metric. When p = 1, this is
        equivalent to using manhattan_distance (l1), and euclidean_distance
        (l2) for p = 2. For arbitrary p, minkowski_distance (l_p) is used.

    metric_params : dict, optional
        additional keyword arguments for the metric function.

    include_self : bool, default=False.
        Whether or not to mark each sample as the first nearest neighbor to
        itself.

    n_jobs : int, optional (default = 1)
        The number of parallel jobs to run for neighbors search.
        If ``-1``, then the number of jobs is set to the number of CPU cores.

    Returns
    -------
    A : sparse matrix in CSR format, shape = [n_samples, n_samples]
        A[i, j] is assigned the weight of edge that connects i to j.

    Examples
    --------
    >>> X = [[0], [3], [1]]
    >>> from sklearn.neighbors import kneighbors_graph
    >>> A = kneighbors_graph(X, 2, mode='connectivity', include_self=True)
    >>> A.toarray()
    array([[ 1.,  0.,  1.],
           [ 0.,  1.,  1.],
           [ 1.,  0.,  1.]])

    See also
    --------
    radius_neighbors_graph
    """
    if not isinstance(X, KNeighborsMixin):
        X = NearestNeighbors(n_neighbors, metric=metric, p=p,
                             metric_params=metric_params, n_jobs=n_jobs).fit(X)
    else:
        _check_params(X, metric, p, metric_params)

    query = _query_include_self(X, include_self)
    return X.kneighbors_graph(X=query, n_neighbors=n_neighbors, mode=mode)


def radius_neighbors_graph(X, radius, mode='connectivity', metric='minkowski',
                           p=2, metric_params=None, include_self=False, n_jobs=1):
    """Computes the (weighted) graph of Neighbors for points in X

    Neighborhoods are restricted the points at a distance lower than
    radius.

    Read more in the :ref:`User Guide <unsupervised_neighbors>`.

    Parameters
    ----------
    X : array-like or BallTree, shape = [n_samples, n_features]
        Sample data, in the form of a numpy array or a precomputed
        :class:`BallTree`.

    radius : float
        Radius of neighborhoods.

    mode : {'connectivity', 'distance'}, optional
        Type of returned matrix: 'connectivity' will return the connectivity
        matrix with ones and zeros, and 'distance' will return the distances
        between neighbors according to the given metric.

    metric : string, default 'minkowski'
        The distance metric used to calculate the neighbors within a
        given radius for each sample point. The DistanceMetric class
        gives a list of available metrics. The default distance is
        'euclidean' ('minkowski' metric with the param equal to 2.)

    p : int, default 2
        Power parameter for the Minkowski metric. When p = 1, this is
        equivalent to using manhattan_distance (l1), and euclidean_distance
        (l2) for p = 2. For arbitrary p, minkowski_distance (l_p) is used.

    metric_params : dict, optional
        additional keyword arguments for the metric function.

    include_self : bool, default=False
        Whether or not to mark each sample as the first nearest neighbor to
        itself.

    n_jobs : int, optional (default = 1)
        The number of parallel jobs to run for neighbors search.
        If ``-1``, then the number of jobs is set to the number of CPU cores.

    Returns
    -------
    A : sparse matrix in CSR format, shape = [n_samples, n_samples]
        A[i, j] is assigned the weight of edge that connects i to j.

    Examples
    --------
    >>> X = [[0], [3], [1]]
    >>> from sklearn.neighbors import radius_neighbors_graph
    >>> A = radius_neighbors_graph(X, 1.5, mode='connectivity', include_self=True)
    >>> A.toarray()
    array([[ 1.,  0.,  1.],
           [ 0.,  1.,  0.],
           [ 1.,  0.,  1.]])

    See also
    --------
    kneighbors_graph
    """
    if not isinstance(X, RadiusNeighborsMixin):
        X = NearestNeighbors(radius=radius, metric=metric, p=p,
                             metric_params=metric_params, n_jobs=n_jobs).fit(X)
    else:
        _check_params(X, metric, p, metric_params)

    query = _query_include_self(X, include_self)
    return X.radius_neighbors_graph(query, radius, mode)


class KNeighborsTransformer(NeighborsBase, KNeighborsMixin,
                            UnsupervisedMixin, TransformerMixin):
    """Transform X into a (weighted) graph of k nearest neighbors

    The transformed data is a sparse graph as return by kneighbors_graph.

    Parameters
    ----------
    mode : {'distance', 'connectivity'}, optional (default = 'connectivity')
        Type of returned matrix: 'connectivity' will return the connectivity
        matrix with ones and zeros, and 'distance' will return the distances
        between neighbors according to the given metric.

    include_self : bool, default=True.
        Whether or not to mark each sample as the first nearest neighbor to
        itself. If None, then True is used for mode='connectivity' and False
        for mode='distance'.

    n_neighbors : int, optional (default = 5)
        Number of neighbors to use for :meth:`kneighbors` queries.

    algorithm : {'auto', 'ball_tree', 'kd_tree', 'brute'}, optional
        Algorithm used to compute the nearest neighbors:

        - 'ball_tree' will use :class:`BallTree`
        - 'kd_tree' will use :class:`KDTree`
        - 'brute' will use a brute-force search.
        - 'auto' will attempt to decide the most appropriate algorithm
          based on the values passed to :meth:`fit` method.

        Note: fitting on sparse input will override the setting of
        this parameter, using brute force.

    leaf_size : int, optional (default = 30)
        Leaf size passed to BallTree or KDTree.  This can affect the
        speed of the construction and query, as well as the memory
        required to store the tree.  The optimal value depends on the
        nature of the problem.

    metric : string or callable, default 'minkowski'
        metric to use for distance computation. Any metric from scikit-learn
        or scipy.spatial.distance can be used.

        If metric is a callable function, it is called on each
        pair of instances (rows) and the resulting value recorded. The callable
        should take two arrays as input and return one value indicating the
        distance between them. This works for Scipy's metrics, but is less
        efficient than passing the metric name as a string.

        Distance matrices are not supported.

        Valid values for metric are:

        - from scikit-learn: ['cityblock', 'cosine', 'euclidean', 'l1', 'l2',
          'manhattan']

        - from scipy.spatial.distance: ['braycurtis', 'canberra', 'chebyshev',
          'correlation', 'dice', 'hamming', 'jaccard', 'kulsinski',
          'mahalanobis', 'minkowski', 'rogerstanimoto', 'russellrao',
          'seuclidean', 'sokalmichener', 'sokalsneath', 'sqeuclidean',
          'yule']

        See the documentation for scipy.spatial.distance for details on these
        metrics.

    p : integer, optional (default = 2)
        Parameter for the Minkowski metric from
        sklearn.metrics.pairwise.pairwise_distances. When p = 1, this is
        equivalent to using manhattan_distance (l1), and euclidean_distance
        (l2) for p = 2. For arbitrary p, minkowski_distance (l_p) is used.

    metric_params : dict, optional (default = None)
        Additional keyword arguments for the metric function.

    n_jobs : int, optional (default = 1)
        The number of parallel jobs to run for neighbors search.
        If ``-1``, then the number of jobs is set to the number of CPU cores.
        Affects only :meth:`kneighbors` and :meth:`kneighbors_graph` methods.

    Examples
    --------
    >>> from sklearn.manifold import Isomap
    >>> from sklearn.neighbors import KNeighborsTransformer
    >>> from sklearn.pipeline import make_pipeline
    >>> estimator = make_pipeline(
    ...     KNeighborsTransformer(n_neighbors=5, mode='distance'),
    ...     Isomap(neighbors_algorithm='precomputed'))
    """
    def __init__(self, mode='connectivity', include_self=None,
                 n_neighbors=5, algorithm='auto', leaf_size=30,
                 metric='minkowski', p=2, metric_params=None, n_jobs=1):
        super(KNeighborsTransformer, self).__init__(
            n_neighbors=n_neighbors, radius=None, algorithm=algorithm,
            leaf_size=leaf_size, metric=metric, p=p,
            metric_params=metric_params, n_jobs=n_jobs)
        self.mode = mode
        self.include_self = include_self

    def transform(self, X):
        """Computes the (weighted) graph of Neighbors for points in X

        Parameters
        ----------
        X : array-like, shape (n_samples_transform, n_features)
            Sample data

        Returns
        -------
        Xt : CSR sparse matrix, shape (n_samples_fit, n_samples_transform)
            Xt[i, j] is assigned the weight of edge that connects i to j.
        """
        check_is_fitted(self, '_fit_X')
        if X is not None:
            check_array(X, accept_sparse='csr')
        return self.kneighbors_graph(X, self.n_neighbors, self.mode)

    def fit_transform(self, X, y=None):
        """Fit to data, then transform it.

        Fits transformer to X and y with optional parameters fit_params
        and returns a transformed version of X.

        Parameters
        ----------
        X : numpy array of shape (n_samples, n_features)
            Training set.

        y : ignored

        Returns
        -------
        Xt : CSR sparse matrix, shape (n_samples, n_samples)
            Xt[i, j] is assigned the weight of edge that connects i to j.
        """
        self.fit(X)

        if self.include_self is None:
            include_self = self.mode == 'connectivity'
        else:
            include_self = self.include_self

        # If we don't include each sample as its own neighbors
        if not include_self:
            X = None
        return self.transform(X)


class RadiusNeighborsTransformer(NeighborsBase, RadiusNeighborsMixin,
                                 UnsupervisedMixin, TransformerMixin):
    """Transform X into a (weighted) graph of neighbors nearer than a radius

    The transformed data is a sparse graph as return by radius_neighbors_graph.

    Parameters
    ----------
    mode : {'distance', 'connectivity'}, optional (default = 'connectivity')
        Type of returned matrix: 'connectivity' will return the connectivity
        matrix with ones and zeros, and 'distance' will return the distances
        between neighbors according to the given metric.

    include_self : bool, default=True.
        Whether or not to mark each sample as the first nearest neighbor to
        itself. If None, then True is used for mode='connectivity' and False
        for mode='distance'.

    radius : float, optional (default = 1.)
        Range of parameter space to use for :meth:`radius_neighbors`

    algorithm : {'auto', 'ball_tree', 'kd_tree', 'brute'}, optional
        Algorithm used to compute the nearest neighbors:

        - 'ball_tree' will use :class:`BallTree`
        - 'kd_tree' will use :class:`KDTree`
        - 'brute' will use a brute-force search.
        - 'auto' will attempt to decide the most appropriate algorithm
          based on the values passed to :meth:`fit` method.

        Note: fitting on sparse input will override the setting of
        this parameter, using brute force.

    leaf_size : int, optional (default = 30)
        Leaf size passed to BallTree or KDTree.  This can affect the
        speed of the construction and query, as well as the memory
        required to store the tree.  The optimal value depends on the
        nature of the problem.

    metric : string or callable, default 'minkowski'
        metric to use for distance computation. Any metric from scikit-learn
        or scipy.spatial.distance can be used.

        If metric is a callable function, it is called on each
        pair of instances (rows) and the resulting value recorded. The callable
        should take two arrays as input and return one value indicating the
        distance between them. This works for Scipy's metrics, but is less
        efficient than passing the metric name as a string.

        Distance matrices are not supported.

        Valid values for metric are:

        - from scikit-learn: ['cityblock', 'cosine', 'euclidean', 'l1', 'l2',
          'manhattan']

        - from scipy.spatial.distance: ['braycurtis', 'canberra', 'chebyshev',
          'correlation', 'dice', 'hamming', 'jaccard', 'kulsinski',
          'mahalanobis', 'minkowski', 'rogerstanimoto', 'russellrao',
          'seuclidean', 'sokalmichener', 'sokalsneath', 'sqeuclidean',
          'yule']

        See the documentation for scipy.spatial.distance for details on these
        metrics.

    p : integer, optional (default = 2)
        Parameter for the Minkowski metric from
        sklearn.metrics.pairwise.pairwise_distances. When p = 1, this is
        equivalent to using manhattan_distance (l1), and euclidean_distance
        (l2) for p = 2. For arbitrary p, minkowski_distance (l_p) is used.

    metric_params : dict, optional (default = None)
        Additional keyword arguments for the metric function.

    n_jobs : int, optional (default = 1)
        The number of parallel jobs to run for neighbors search.
        If ``-1``, then the number of jobs is set to the number of CPU cores.
        Affects only :meth:`kneighbors` and :meth:`kneighbors_graph` methods.

    Examples
    --------
    >>> from sklearn.cluster import DBSCAN
    >>> from sklearn.neighbors import RadiusNeighborsTransformer
    >>> from sklearn.pipeline import make_pipeline
    >>> estimator = make_pipeline(
    ...     RadiusNeighborsTransformer(radius=42.0, mode='distance'),
    ...     DBSCAN(min_samples=30, metric='precomputed'))
    """
    def __init__(self, mode='connectivity', include_self=None,
                 radius=1., algorithm='auto', leaf_size=30,
                 metric='minkowski', p=2, metric_params=None, n_jobs=1):
        super(RadiusNeighborsTransformer, self).__init__(
            n_neighbors=None, radius=radius, algorithm=algorithm,
            leaf_size=leaf_size, metric=metric, p=p,
            metric_params=metric_params, n_jobs=n_jobs)
        self.mode = mode
        self.include_self = include_self

    def transform(self, X):
        """Computes the (weighted) graph of Neighbors for points in X

        Parameters
        ----------
        X : array-like, shape (n_samples_transform, n_features)
            Sample data

        Returns
        -------
        Xt : CSR sparse matrix, shape (n_samples_fit, n_samples_transform)
            Xt[i, j] is assigned the weight of edge that connects i to j.
        """
        check_is_fitted(self, '_fit_X')
        if X is not None:
            check_array(X, accept_sparse='csr')
        return self.radius_neighbors_graph(X, self.radius, self.mode)

    def fit_transform(self, X, y=None):
        """Fit to data, then transform it.

        Fits transformer to X and y with optional parameters fit_params
        and returns a transformed version of X.

        Parameters
        ----------
        X : numpy array of shape (n_samples, n_features)
            Training set.

        y : ignored

        Returns
        -------
        Xt : CSR sparse matrix, shape (n_samples, n_samples)
            Xt[i, j] is assigned the weight of edge that connects i to j.
        """
        self.fit(X)

        if self.include_self is None:
            include_self = self.mode == 'connectivity'
        else:
            include_self = self.include_self

        # If we don't include each sample as its own neighbors
        if not include_self:
            X = None
        return self.transform(X)
