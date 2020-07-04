"""
Testing for the subsampled module.
"""

import numpy as np
from scipy.sparse import csr_matrix
from numpy.testing import assert_array_equal, assert_almost_equal

from sklearn.neighbors import SubsampledNeighborsTransformer
from sklearn import datasets
from sklearn.utils._testing import assert_array_almost_equal, assert_raises

# Toy samples
X = [[1, 2, 3], [2, 3, 4], [3, 4, 5], [6, 7, 8]]
X_csr = csr_matrix(X) 
X2 = [[6], [5], [4], [3]]
X2_csr = csr_matrix(X2)

# Load the iris dataset and randomly permute it
iris = datasets.load_iris()
rng = np.random.RandomState(1)
perm = rng.permutation(iris.target.size)
iris.data = iris.data[perm]
iris.target = iris.target[perm]
n_iris = iris.data.shape[0]

def test_sample_toy_fit_nonsparse_transform_nonsparse():
    # Fit and transform with non-sparse
    n = SubsampledNeighborsTransformer(1.0, random_state=0)
    expected_result = csr_matrix(([1.732051, 3.464102, 8.660254, 1.732051, 3.464102, 5.196152, 
        8.660254, 5.196152], ([0, 0, 0, 1, 2, 2, 3, 3], [1, 2, 3, 0, 0, 3, 0, 2])), shape=(4, 4))
    assert_array_almost_equal(n.fit_transform(X).toarray(), expected_result.toarray())
    expected_result = csr_matrix(([1., 2., 3., 1., 2., 1., 3., 1.], ([0, 0, 0, 1, 2, 2, 3, 3], 
        [1, 2, 3, 0, 0, 3, 0, 2])), shape=(4, 4))
    assert_array_equal(n.fit_transform(X2).toarray(), expected_result.toarray())


def test_sample_toy_fit_sparse_transform_sparse():
    # Fit and transform with sparse
    n = SubsampledNeighborsTransformer(0.2, random_state=1)
    expected_result = csr_matrix(([6.928203, 6.928203], ([1, 3], [3, 1])), shape=(4, 4))
    assert_array_almost_equal(n.fit(X_csr).transform(X).toarray(), expected_result.toarray())
    expected_result = csr_matrix(([2., 2.], ([1, 3], [3, 1])), shape=(4, 4))
    assert_array_equal(n.fit(X2_csr).transform(X2).toarray(), expected_result.toarray())


def test_sample_toy_fit_sparse_transform_nonsparse():
    # Fit with sparse, test with non-sparse
    n = SubsampledNeighborsTransformer(0.9, random_state=2)
    expected_result = csr_matrix(([3.464102, 8.660254, 1.732051, 6.928203, 3.464102, 
          1.732051, 5.196152, 8.660254, 6.928203, 5.196152], ([0, 0, 1, 1, 2, 2, 2, 3, 3, 3], 
          [2, 3, 2, 3, 0, 1, 3, 0, 1, 2])), shape=(4, 4))
    assert_array_almost_equal(n.fit(X_csr).transform(X).toarray(), expected_result.toarray())
    expected_result = csr_matrix(([2., 3., 1., 2., 2., 1., 1., 3., 2., 1.], ([0, 0, 1, 1, 2, 2, 2, 3, 3, 3], 
        [2, 3, 2, 3, 0, 1, 3, 0, 1, 2])), shape=(4, 4))
    assert_array_equal(n.fit(X_csr).transform(X2).toarray(), expected_result.toarray())


def test_sample_toy_fit_nonsparse_transform_sparse():
    # Fit with non-sparse, test with sparse
    n = SubsampledNeighborsTransformer(0.3, random_state=3)
    expected_result = csr_matrix(([8.660254, 1.732051, 1.732051, 8.660254], 
        ([0, 1, 2, 3], [3, 2, 1, 0])), shape=(4, 4))
    assert_array_almost_equal(n.fit(X).transform(X_csr).toarray(), expected_result.toarray())
    expected_result = csr_matrix(([3., 1., 1., 3.], ([0, 1, 2, 3], [3, 2, 1, 0])), shape=(4, 4))
    assert_array_equal(n.fit(X2).transform(X2_csr).toarray(), expected_result.toarray())


def test_sample_toy_noncsr(): 
    # Fit and transform with non-CSR sparse matrices
    n = SubsampledNeighborsTransformer(0.8, random_state=4)
    expected_result = csr_matrix(([3.464102, 1.732051, 3.464102, 1.732051, 5.196152, 5.196152], 
        ([0, 1, 2, 2, 2, 3], [2, 2, 0, 1, 3, 2])), shape=(4, 4))
    assert_array_almost_equal(n.fit(X_csr.tocoo()).transform(X_csr.tolil()).toarray(), expected_result.toarray())
    expected_result = csr_matrix(([2., 1., 2., 1., 1., 1.], ([0, 1, 2, 2, 2, 3], [2, 2, 0, 1, 3, 2])), 
        shape=(4, 4))
    assert_array_equal(n.fit(X2_csr.todok()).transform(X2_csr.tocsc()).toarray(), expected_result.toarray())


def test_sample_toy_no_edges():
    # Sampling rate too low
    n = SubsampledNeighborsTransformer(0.1, random_state=5)
    expected_result = csr_matrix(([], ([], [])), shape=(4, 4))
    assert_array_almost_equal(n.fit_transform(X).toarray(), expected_result.toarray())
    expected_result = csr_matrix(([], ([], [])), shape=(4, 4))
    assert_array_equal(n.fit_transform(X2_csr).toarray(), expected_result.toarray())


def test_invalid_s():
    # Invalid s
    n = SubsampledNeighborsTransformer(-1)
    assert_raises(ValueError, n.fit_transform, X)
    assert_raises(ValueError, n.fit_transform, X2)


def test_invalid_metric():
    # Invalid metric
    n = SubsampledNeighborsTransformer(0.7, metric='invalid')
    assert_raises(ValueError, n.fit_transform, X)
    assert_raises(ValueError, n.fit_transform, X2)

    # Invalid metric and sampling rate too low
    n = SubsampledNeighborsTransformer(0.01, metric='invalid')
    assert_raises(ValueError, n.fit_transform, X)
    assert_raises(ValueError, n.fit_transform, X2)


def test_iris_euclidean():
    # Euclidean distance
    n = SubsampledNeighborsTransformer(0.4, metric='euclidean', random_state=42)
    assert_almost_equal(np.mean(n.fit(iris.data).transform(iris.data)), 0.8374589)


def test_iris_cosine():
    # Cosine distance
    n = SubsampledNeighborsTransformer(0.6, metric='cosine', random_state=42)
    assert_almost_equal(np.mean(n.fit(iris.data).transform(iris.data)), 0.0200056)


def test_iris_manhattan():
    # Manhattan distance
    n = SubsampledNeighborsTransformer(0.5, metric='manhattan', random_state=42)
    assert_almost_equal(np.mean(n.fit_transform(iris.data)), 1.6821866)


def test_iris_small_s():
    # Small s
    n = SubsampledNeighborsTransformer(0.0001, random_state=42)
    expected_result = csr_matrix(([5.853204, 5.853204], ([92, 102], [102, 92])), shape=(n_iris, n_iris))
    assert_array_almost_equal(n.fit_transform(iris.data).toarray(), expected_result.toarray())


def test_iris_large_s():
    # Large s
    n = SubsampledNeighborsTransformer(2.0, random_state=42)
    print(np.mean(n.fit_transform(iris.data)))
    assert_almost_equal(np.mean(n.fit_transform(iris.data)), 2.17207055)


def test_iris_no_edges():
    # No edges
    n = SubsampledNeighborsTransformer(0.00001)
    expected_result = csr_matrix(([], ([], [])), shape=(n_iris, n_iris))
    assert_array_almost_equal(n.fit_transform(iris.data).toarray(), expected_result.toarray())

