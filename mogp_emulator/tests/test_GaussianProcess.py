from tempfile import TemporaryFile
import numpy as np
import pytest
from numpy.testing import assert_allclose
from .. import GaussianProcess
from scipy import linalg

def test_GaussianProcess_init():
    "Test function for correct functioning of the init method of GaussianProcess"
    
    x = np.reshape(np.array([1., 2., 3.]), (1, 3))
    y = np.array([2.])
    gp = GaussianProcess(x, y)
    assert_allclose(x, gp.inputs)
    assert_allclose(y, gp.targets)
    assert gp.D == 3
    assert gp.n == 1
    
    x = np.reshape(np.array([1., 2., 3., 4., 5., 6.]), (3, 2))
    y = np.array([2., 3., 4.])
    gp = GaussianProcess(x, y)
    assert_allclose(x, gp.inputs)
    assert_allclose(y, gp.targets)
    assert gp.D == 2
    assert gp.n == 3
    
    x = np.array([1., 2., 3., 4., 5., 6.])
    y = np.array([2.])
    gp = GaussianProcess(x, y)
    assert_allclose(np.array([x]), gp.inputs)
    assert_allclose(y, gp.targets)
    assert gp.D == 6
    assert gp.n == 1

def test_GaussianProcess_init_failures():
    "Tests that GaussianProcess fails correctly with bad inputs"
    
    x = np.reshape(np.array([1., 2., 3.]), (1, 3))
    y = np.array([2.])
    z = np.array([4.])
    with pytest.raises(ValueError):
        gp = GaussianProcess(x, y, z)
        
    x = np.array([1., 2., 3., 4., 5., 6.])
    y = np.array([2., 3.])
    with pytest.raises(ValueError):
        gp = GaussianProcess(x, y)
        
    x = np.array([[1., 2., 3.], [4., 5., 6.]])
    y = np.array([2., 3., 4.])
    with pytest.raises(ValueError):
        gp = GaussianProcess(x, y)
        
    x = np.array([[1., 2., 3.]])
    y = np.array([[2., 3.], [4., 5]])
    with pytest.raises(ValueError):
        gp = GaussianProcess(x, y)

def test_GaussianProcess_jit_cholesky():
    "Tests the stabilized Cholesky decomposition routine in Gaussian Process"
    x = np.reshape(np.array([1., 2., 3., 4., 5., 6.]), (3, 2))
    y = np.array([2., 3., 4.])
    gp = GaussianProcess(x, y)
    
    expected = np.array([[2., 0., 0.], [6., 1., 0.], [-8., 5., 3.]])
    input_matrix = np.array([[4., 12., -16.], [12., 37., -43.], [-16., -43., 98.]])
    assert_allclose(expected, gp._jit_cholesky(input_matrix))
    
    expected = np.array([[1.0000004999998751e+00, 0.0000000000000000e+00, 0.0000000000000000e+00],
                         [9.9999950000037496e-01, 1.4142132088085626e-03, 0.0000000000000000e+00],
                         [6.7379436301144941e-03, 4.7644444411381860e-06, 9.9997779980004420e-01]])
    input_matrix = np.array([[1.                , 1.                , 0.0067379469990855],
                             [1.                , 1.                , 0.0067379469990855],
                             [0.0067379469990855, 0.0067379469990855, 1.                ]])
    assert_allclose(expected, gp._jit_cholesky(input_matrix))
    
    input_matrix = np.array([[1.e-6, 1., 0.], [1., 1., 1.], [0., 1., 1.e-10]])
    with pytest.raises(linalg.LinAlgError):
        gp._jit_cholesky(input_matrix)
        
    input_matrix = np.array([[-1., 2., 2.], [2., 3., 2.], [2., 2., -3.]])
    with pytest.raises(linalg.LinAlgError):
        gp._jit_cholesky(input_matrix)

def test_GaussianProcess_prepare_likelihood():
    "Tests the _prepare_likelihood method of Gaussian Process"
    
    x = np.reshape(np.array([1., 2., 3., 2., 4., 1., 4., 2., 2.]), (3, 3))
    y = np.array([2., 3., 4.])
    gp = GaussianProcess(x, y)
    theta = np.zeros(4)
    invQ_expected = np.array([[ 1.000167195256076 , -0.0110373516824135, -0.0066164596502281],
                              [-0.0110373516824135,  1.0002452278032625, -0.0110373516824135],
                              [-0.0066164596502281, -0.0110373516824135,  1.0001671952560762]])
    invQt_expected = np.array([1.9407564968639992, 2.934511573315307 , 3.954323806676608 ])
    logdetQ_expected = -0.00029059870020992285
    gp.theta = theta
    gp._prepare_likelihood()
    assert_allclose(gp.invQ, invQ_expected)
    assert_allclose(gp.invQt, invQt_expected)
    assert_allclose(gp.logdetQ, logdetQ_expected)
    
    x = np.reshape(np.array([1., 2., 3., 1., 2., 3., 4., 2., 2.]), (3, 3))
    y = np.array([2., 3., 4.])
    gp = GaussianProcess(x, y)
    theta = np.zeros(4)
    gp.theta = theta
    gp._prepare_likelihood()
    invQ_expected = np.array([[ 5.0000025001932273e+05, -4.9999974999687175e+05, -3.3691214036059968e-03],
                              [-4.9999974999687175e+05,  5.0000025001932273e+05, -3.3691214038620732e-03],
                              [-3.3691214036059972e-03, -3.3691214038620732e-03, 1.0000444018785022e+00]])
    invQt_expected = np.array([-4.9999876342845545e+05,  5.0000123658773920e+05, 3.9833320004952104e+00])
    logdetQ_expected = -13.122407278313416
    assert_allclose(gp.invQ, invQ_expected)
    assert_allclose(gp.invQt, invQt_expected)
    assert_allclose(gp.logdetQ, logdetQ_expected)

def test_GaussianProcess_set_params():
    "Tests the _set_params method of GaussianProcess"
    
    x = np.reshape(np.array([1., 2., 3., 2., 4., 1., 4., 2., 2.]), (3, 3))
    y = np.array([2., 3., 4.])
    gp = GaussianProcess(x, y)
    theta = np.zeros(4)
    invQ_expected = np.array([[ 1.000167195256076 , -0.0110373516824135, -0.0066164596502281],
                              [-0.0110373516824135,  1.0002452278032625, -0.0110373516824135],
                              [-0.0066164596502281, -0.0110373516824135,  1.0001671952560762]])
    invQt_expected = np.array([1.9407564968639992, 2.934511573315307 , 3.954323806676608 ])
    logdetQ_expected = -0.00029059870020992285
    gp._set_params(theta)
    assert_allclose(theta, gp.theta)
    assert_allclose(gp.invQ, invQ_expected)
    assert_allclose(gp.invQt, invQt_expected)
    assert_allclose(gp.logdetQ, logdetQ_expected)
    
    x = np.reshape(np.array([1., 2., 3., 2., 4., 1., 4., 2., 2.]), (3, 3))
    y = np.array([2., 3., 4.])
    gp = GaussianProcess(x, y)
    theta = np.zeros(5)
    with pytest.raises(AssertionError):
        gp._set_params(theta)

def test_GaussianProcess_loglikelihood():
    "Test the loglikelihood method of GaussianProcess"
    x = np.reshape(np.array([1., 2., 3., 2., 4., 1., 4., 2., 2.]), (3, 3))
    y = np.array([2., 3., 4.])
    gp = GaussianProcess(x, y)
    theta = np.zeros(4)
    expected_loglikelihood = 17.00784177045409
    actual_loglikelihood = gp.loglikelihood(theta)
    assert_allclose(actual_loglikelihood, expected_loglikelihood)
    assert_allclose(gp.theta, theta)
    assert_allclose(gp.current_loglikelihood, expected_loglikelihood)
    assert_allclose(gp.current_theta, theta)
    
    x = np.reshape(np.array([1., 2., 3., 2., 4., 1., 4., 2., 2.]), (3, 3))
    y = np.array([2., 3., 4.])
    gp = GaussianProcess(x, y)
    theta = np.zeros(5)
    with pytest.raises(AssertionError):
        gp.loglikelihood(theta)

def test_GaussianProcess_get_n():
    "Tests the get_n method of GaussianProcess"
    x = np.reshape(np.array([1., 2., 3.]), (1, 3))
    y = np.array([2.])
    gp = GaussianProcess(x, y)
    assert gp.get_n() == 1

def test_GaussianProcess_get_D():
    "Tests the get_D method of Gaussian Process"
    x = np.reshape(np.array([1., 2., 3.]), (1, 3))
    y = np.array([2.])
    gp = GaussianProcess(x, y)
    assert gp.get_D() == 3

def test_GaussianProcess_str():
    "Test function for string method"
    x = np.reshape(np.array([1., 2., 3.]), (1, 3))
    y = np.array([2.])
    gp = GaussianProcess(x, y)
    assert (str(gp) == "Gaussian Process with 1 training examples and 3 input variables")