from __future__ import absolute_import

import pytest
import numpy as np
import scipy.sparse as sp
import warnings

from sklearn.externals.six.moves import xrange as range
from sklearn.preprocessing import KBinsDiscretizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.utils.testing import (
    assert_array_equal,
    assert_raises,
    assert_raise_message,
    assert_warns_message
)

X = [[-2, 1.5, -4, -1],
     [-1, 2.5, -3, -0.5],
     [0, 3.5, -2, 0.5],
     [1, 4.5, -1, 2]]


@pytest.mark.parametrize(
    'strategy, expected',
    [('uniform', [[0, 0, 0, 0], [1, 1, 1, 0], [2, 2, 2, 1], [2, 2, 2, 2]]),
     ('kmeans', [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2]]),
     ('quantile', [[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2], [2, 2, 2, 2]])])
def test_fit_transform(strategy, expected):
    est = KBinsDiscretizer(n_bins=3, encode='ordinal', strategy=strategy)
    est.fit(X)
    assert_array_equal(expected, est.transform(X))


def test_valid_n_bins():
    KBinsDiscretizer(n_bins=2).fit_transform(X)
    KBinsDiscretizer(n_bins=np.array([2])[0]).fit_transform(X)
    assert KBinsDiscretizer(n_bins=2).fit(X).n_bins_.dtype == np.dtype(np.int)


def test_invalid_n_bins():
    est = KBinsDiscretizer(n_bins=1)
    assert_raise_message(ValueError, "KBinsDiscretizer received an invalid "
                         "number of bins. Received 1, expected at least 2.",
                         est.fit_transform, X)

    est = KBinsDiscretizer(n_bins=1.1)
    assert_raise_message(ValueError, "KBinsDiscretizer received an invalid "
                         "n_bins type. Received float, expected int.",
                         est.fit_transform, X)


def test_invalid_n_bins_array():
    # Bad shape
    n_bins = np.ones((2, 4)) * 2
    est = KBinsDiscretizer(n_bins=n_bins)
    assert_raise_message(ValueError,
                         "n_bins must be a scalar or array of shape "
                         "(n_features,).", est.fit_transform, X)

    # Incorrect number of features
    n_bins = [1, 2, 2]
    est = KBinsDiscretizer(n_bins=n_bins)
    assert_raise_message(ValueError,
                         "n_bins must be a scalar or array of shape "
                         "(n_features,).", est.fit_transform, X)

    # Bad bin values
    n_bins = [1, 2, 2, 1]
    est = KBinsDiscretizer(n_bins=n_bins)
    assert_raise_message(ValueError,
                         "KBinsDiscretizer received an invalid number of bins "
                         "at indices 0, 3. Number of bins must be at least 2, "
                         "and must be an int.",
                         est.fit_transform, X)

    # Float bin values
    n_bins = [2.1, 2, 2.1, 2]
    est = KBinsDiscretizer(n_bins=n_bins)
    assert_raise_message(ValueError,
                         "KBinsDiscretizer received an invalid number of bins "
                         "at indices 0, 2. Number of bins must be at least 2, "
                         "and must be an int.",
                         est.fit_transform, X)


@pytest.mark.parametrize(
    'strategy, expected',
    [('uniform', [[0, 0, 0, 0], [0, 1, 1, 0], [1, 2, 2, 1], [1, 2, 2, 2]]),
     ('kmeans', [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], [1, 2, 2, 2]]),
     ('quantile', [[0, 0, 0, 0], [0, 1, 1, 1], [1, 2, 2, 2], [1, 2, 2, 2]])])
def test_fit_transform_n_bins_array(strategy, expected):
    est = KBinsDiscretizer(n_bins=[2, 3, 3, 3], encode='ordinal',
                           strategy=strategy).fit(X)
    assert_array_equal(expected, est.transform(X))

    # test the shape of bin_edges_
    n_features = np.array(X).shape[1]
    assert est.bin_edges_.shape == (n_features, )
    for bin_edges, n_bins in zip(est.bin_edges_, est.n_bins_):
        assert bin_edges.shape == (n_bins + 1, )


def test_invalid_n_features():
    est = KBinsDiscretizer(n_bins=3).fit(X)
    bad_X = np.arange(25).reshape(5, -1)
    assert_raise_message(ValueError,
                         "Incorrect number of features. Expecting 4, "
                         "received 5", est.transform, bad_X)


@pytest.mark.parametrize(
    'strategy, expected',
    [('uniform', [[0., 1.5, 0., 0.], [1., 2.5, 1., 0.],
                  [2., 3.5, 2., 1.], [2., 4.5, 2., 2.]]),
     ('kmeans', [[0., 1.5, 0., 0.], [0., 2.5, 0., 0.],
                 [1., 3.5, 1., 1.], [2., 4.5, 2., 2.]]),
     ('quantile', [[0., 1.5, 0., 0.], [1., 2.5, 1., 1.],
                   [2., 3.5, 2., 2.], [2., 4.5, 2., 2.]])])
def test_ignored_transform(strategy, expected):
    # Feature at col_idx=1 should not change
    est = KBinsDiscretizer(n_bins=3, ignored_features=[1],
                           encode='ordinal', strategy=strategy).fit(X)
    assert_array_equal(expected, est.transform(X))


def test_ignored_invalid():
    # Duplicate column
    est = KBinsDiscretizer(ignored_features=[1, 1])
    assert_raise_message(ValueError, "Duplicate ignored column indices found.",
                         est.fit, X)

    invalid_ignored = [
        [-1],  # Invalid index
        [4],  # Invalid index
        ['a'],  # Not an integer index
        [4.5],  # Not an integer index
        [[1, 2], [3, 4]]  # Invalid shape
    ]

    for invalid in invalid_ignored:
        est = KBinsDiscretizer(ignored_features=invalid)
        assert_raises(ValueError, est.fit, X)


@pytest.mark.parametrize('strategy', ['uniform', 'kmeans', 'quantile'])
def test_same_min_max(strategy):
    warnings.simplefilter("always")
    X = np.array([[1, -2],
                  [1, -1],
                  [1, 0],
                  [1, 1]])
    est = KBinsDiscretizer(strategy=strategy, n_bins=3, encode='ordinal')
    assert_warns_message(UserWarning,
                         "Feature 0 is constant and will be replaced "
                         "with 0.", est.fit, X)
    assert est.n_bins_[0] == 1
    # replace the feature with zeros
    Xt = est.transform(X)
    assert_array_equal(Xt[:, 0], np.zeros(X.shape[0]))


def test_transform_1d_behavior():
    X = np.arange(4)
    est = KBinsDiscretizer(n_bins=2)
    assert_raises(ValueError, est.fit, X)

    est = KBinsDiscretizer(n_bins=2)
    est.fit(X.reshape(-1, 1))
    assert_raises(ValueError, est.transform, X)


def test_inverse_transform_with_ignored():
    est = KBinsDiscretizer(n_bins=[2, 3, 0, 3], ignored_features=[1, 2],
                           encode='ordinal', strategy='uniform').fit(X)
    Xt = [[0, 1, -4.5, 0],
          [0, 2, -3.5, 0],
          [1, 3, -2.5, 1],
          [1, 3, -1.5, 2]]

    Xinv = est.inverse_transform(Xt)
    expected = [[-1.25, 1, -4.5, -0.5],
                [-1.25, 2, -3.5, -0.5],
                [0.25, 3, -2.5, 0.5],
                [0.25, 3, -1.5, 1.5]]

    assert_array_equal(expected, Xinv)


def test_numeric_stability():
    X_init = np.array([2., 4., 6., 8., 10.]).reshape(-1, 1)
    Xt_expected = np.array([0, 0, 1, 1, 1]).reshape(-1, 1)

    # Test up to discretizing nano units
    for i in range(1, 9):
        X = X_init / 10**i
        Xt = KBinsDiscretizer(n_bins=2, encode='ordinal').fit_transform(X)
        assert_array_equal(Xt_expected, Xt)


def test_invalid_encode_option():
    est = KBinsDiscretizer(n_bins=[2, 3, 3, 3], encode='invalid-encode')
    assert_raise_message(ValueError, "Valid options for 'encode' are "
                         "('onehot', 'onehot-dense', 'ordinal'). "
                         "Got encode='invalid-encode' instead.",
                         est.fit, X)


def test_encode_options():
    est = KBinsDiscretizer(n_bins=[2, 3, 3, 3],
                           encode='ordinal').fit(X)
    Xt_1 = est.transform(X)
    est = KBinsDiscretizer(n_bins=[2, 3, 3, 3],
                           encode='onehot-dense').fit(X)
    Xt_2 = est.transform(X)
    assert not sp.issparse(Xt_2)
    assert_array_equal(OneHotEncoder(n_values=[2, 3, 3, 3], sparse=False)
                       .fit_transform(Xt_1), Xt_2)
    assert_raise_message(ValueError, "inverse_transform only supports "
                         "'encode = ordinal'. Got encode='onehot-dense' "
                         "instead.", est.inverse_transform, Xt_2)
    est = KBinsDiscretizer(n_bins=[2, 3, 3, 3],
                           encode='onehot').fit(X)
    Xt_3 = est.transform(X)
    assert sp.issparse(Xt_3)
    assert_array_equal(OneHotEncoder(n_values=[2, 3, 3, 3], sparse=True)
                       .fit_transform(Xt_1).toarray(),
                       Xt_3.toarray())
    assert_raise_message(ValueError, "inverse_transform only supports "
                         "'encode = ordinal'. Got encode='onehot' "
                         "instead.", est.inverse_transform, Xt_2)


def test_one_hot_encode_with_ignored_features():
    est = KBinsDiscretizer(n_bins=3, ignored_features=[1, 2],
                           encode='onehot-dense', strategy='uniform').fit(X)
    Xt = est.transform(X)
    Xt_expected = [[1, 0, 0, 1, 0, 0, 1.5, -4],
                   [0, 1, 0, 1, 0, 0, 2.5, -3],
                   [0, 0, 1, 0, 1, 0, 3.5, -2],
                   [0, 0, 1, 0, 0, 1, 4.5, -1]]
    assert_array_equal(Xt_expected, Xt)


def test_invalid_strategy_option():
    est = KBinsDiscretizer(n_bins=[2, 3, 3, 3], strategy='invalid-strategy')
    assert_raise_message(ValueError, "Valid options for 'strategy' are "
                         "('uniform', 'quantile', 'kmeans'). "
                         "Got strategy='invalid-strategy' instead.",
                         est.fit, X)


@pytest.mark.parametrize(
    'strategy, expected_2bins, expected_3bins',
    [('uniform', [0, 0, 0, 0, 1, 1], [0, 0, 0, 0, 2, 2]),
     ('kmeans', [0, 0, 0, 0, 1, 1], [0, 1, 1, 1, 2, 2]),
     ('quantile', [0, 0, 0, 1, 1, 1], [0, 0, 1, 1, 2, 2])])
def test_nonuniform_strategies(strategy, expected_2bins, expected_3bins):
    X = np.array([0, 1, 2, 3, 9, 10]).reshape(-1, 1)

    # with 2 bins
    est = KBinsDiscretizer(n_bins=2, strategy=strategy, encode='ordinal')
    Xt = est.fit_transform(X)
    assert_array_equal(expected_2bins, Xt.ravel())

    # with 3 bins
    est = KBinsDiscretizer(n_bins=3, strategy=strategy, encode='ordinal')
    Xt = est.fit_transform(X)
    assert_array_equal(expected_3bins, Xt.ravel())


@pytest.mark.parametrize('strategy', ['uniform', 'kmeans', 'quantile'])
def test_inverse_transform(strategy):
    X = np.random.RandomState(0).randn(100, 3)
    kbd = KBinsDiscretizer(n_bins=3, strategy=strategy, encode='ordinal')
    Xt = kbd.fit_transform(X)
    assert_array_equal(Xt.max(axis=0) + 1, kbd.n_bins_)

    X2 = kbd.inverse_transform(Xt)
    X2t = kbd.fit_transform(X2)
    assert_array_equal(X2t.max(axis=0) + 1, kbd.n_bins_)
    assert_array_equal(Xt, X2t)


@pytest.mark.parametrize('strategy', ['uniform', 'kmeans', 'quantile'])
def test_transform_outside_fit_range(strategy):
    X = np.array([0, 1, 2, 3])[:, None]
    kbd = KBinsDiscretizer(n_bins=4, strategy=strategy, encode='ordinal')
    kbd.fit(X)

    X2 = np.array([-2, 5])[:, None]
    X2t = kbd.transform(X2)
    assert_array_equal(X2t.max(axis=0) + 1, kbd.n_bins_)
    assert_array_equal(X2t.min(axis=0), [0])
