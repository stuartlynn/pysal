# coding=utf-8
"""
 Wilsonian (1967) family of gravity-type spatial interaction models

References
----------

Fotheringham, A. S. and O'Kelly, M. E. (1989). Spatial Interaction Models: Formulations
 and Applications. London: Kluwer Academic Publishers.

Wilson, A. G. (1967). A statistical theory of spatial distribution models.
 Transportation Research, 1, 253–269.

"""

__author__ = "Taylor Oshan tayoshan@gmail.com"

from types import FunctionType
import numpy as np
from scipy import sparse as sp
import statsmodels.api as sm
from statsmodels.api import families 
from statsmodels.tools.tools import categorical
from sparse_categorical import spcategorical
from pysal.spreg import user_output as User
from count_model import CountModel

class BaseGravity(CountModel):
    """
    Base class to set up attributes common across the family of gravity-type
    spatial interaction models

    Parameters
    ----------
    flows           : array of integers
                      n x 1; observed flows between O origins and D destinations
    origins         : array of strings
                      n x 1; unique identifiers of origins of n flows
    destinations    : array of strings
                      n x 1; unique identifiers of destinations of n flows 
    cost            : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cost_func       : string
                      functional form of the cost function; default is 'pow'
                      'exp' | 'pow'
    o_vars          : array (optional)
                      n x k; k attributes for each origin of  n flows; default
                      is None
    d_vars          : array (optional)
                      n x k; k attributes for each destination of n flows;
                      default is None

    Attributes
    ----------
    f               : array
                      n x 1; observed flows; dependent variable; y
    n               : integer
                      number of observations
    c               : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cf              : function
                      cost function; used to transform cost variable
    ov              : array 
                      n x k; k attributes for each origin of n flows
    dv              : array
                      n x k; k attributes for each destination of n flows
    params        : array
                    n*k, estimared beta coefficients
    yhat          : array
                    n*1, predicted value of y (i.e., fittedvalues)
    cov_params    : array
                    Variance covariance matrix (kxk) of betas
    std_err       : array
                    k*1, standard errors of betas
    pvalues       : array
                    k*1, two-tailed pvalues of parameters
    tvalues       : array
                    k*1, the tvalues of the standard errors
    deviance      : float
                    value of the deviance function evalued at params;
                    see family.py for distribution-specific deviance
    llf           : float
                    value of the loglikelihood function evalued at params;
                    see family.py for distribution-specific loglikelihoods
    aic           : float 
                    Akaike information criterion
    results       : object
                    Full results from estimated model. May contain addtional
                    diagnostics
    Example
    -------
    TODO

    """
    def __init__(self, flows, cost, cost_func='pow', o_vars=None, d_vars=None,
            origins=None, destinations=None, constant=False, framework='GLM',
            SF=None, CD=None, Lag=None, Quasi=False):
        n = User.check_arrays(flows, cost)
        User.check_y(flows, n)
        self.n = n
        self.f = flows
        self.c = cost
        self.ov = o_vars
        self.dv = d_vars

        if type(cost_func) == str:
            if cost_func.lower() == 'pow':
                self.cf = np.log
            elif cost_func.lower() == 'exp':
                self.cf = lambda x: x*1.0
        elif type(cost_func) == FunctionType:
            self.cf = cost_func
        else:
            raise ValueError('cost_func must be "exp", "power" or a valid\
            function that has a scalar as a input and output')

        y = np.reshape(self.f, (-1,1))
        if isinstance(self,  Gravity):
            X = np.empty((self.n, 0))
        else:
            X = sp.csr_matrix((self.n, 1))
        if isinstance(self, Attraction) | isinstance(self, Doubly):
            d_dummies = spcategorical(destinations.flatten().astype(str))
            X = sp.hstack((X, d_dummies))
        if isinstance(self, Production) | isinstance(self, Doubly):
            o_dummies = spcategorical(origins.flatten().astype(str)) 
            X = sp.hstack((X, o_dummies))
        if isinstance(self, Doubly):
            X = sp.csr_matrix(X)
            X = X[:,1:]
        if self.ov is not None:	
            if isinstance(self, Gravity):
                X = np.hstack((X, np.log(np.reshape(self.ov, (-1,1)))))
            else:
                ov = sp.csr_matrix(np.log(np.reshape(self.ov, ((-1,1)))))
                X = sp.hstack((X, ov))
        if self.dv is not None:    	
            if isinstance(self, Gravity):
                X = np.hstack((X, np.log(np.reshape(self.dv, (-1,1)))))
            else:
                dv = sp.csr_matrix(np.log(np.reshape(self.dv, ((-1,1)))))
                X = sp.hstack((X, dv))
        if isinstance(self, Gravity):
            X = np.hstack((X, self.cf(np.reshape(self.c, (-1,1)))))
        else:
            c = sp.csr_matrix(self.cf(np.reshape(self.c, (-1,1))))
            X = sp.hstack((X, c))
            X = sp.csr_matrix(X)
            X = X[:,1:]
        if not isinstance(self, (Gravity, Production, Attraction, Doubly)):
            X = self.cf(np.reshape(self.c, (-1,1)))

        if SF:
        	raise NotImplementedError('Spatial filter model not yet implemented')
        if CD:
        	raise NotImplementedError('Competing destination model not yet implemented')
        if Lag:
        	raise NotImplementedError('Spatial Lag autoregressive model not yet implemented')
        
        CountModel.__init__(self, y, X, constant=constant)
        if (framework.lower() == 'glm'):
            if not Quasi:
                results = self.fit(framework='glm')
            else:
                results = self.fit(framework='glm', Quasi=True)
        else:
            raise NotImplementedError('Only GLM is currently implemented')

        self.params = results.params
        self.yhat = results.yhat
        self.cov_params = results.cov_params
        self.std_err = results.std_err
        self.pvalues = results.pvalues
        self.tvalues = results.tvalues
        self.deviance = results.deviance
        self.llf = results.llf
        self.aic = results.aic
        self.full_results = results

    def reshape(self, array):
        if type(array) == np.ndarray:
            return array.reshape((-1,1))
        else:
            raise TypeError('input must be an numpy array that can be coerced"
                    " into the dimensions n x 1')
    
class Gravity(BaseGravity):
    """
    Unconstrained (traditional gravity) gravity-type spatial interaction model

    Parameters
    ----------
    flows           : array of integers
                      n x 1; observed flows between O origins and D destinations
    cost            : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cost_func       : string
                      functional form of the cost function; default is 'pow'
                      'exp' | 'pow'
    o_vars          : array (optional)
                      n x k; k attributes for each origin of  n flows; default
                      is None
    d_vars          : array (optional)
                      n x k; k attributes for each destination of n flows;
                      default is None

    Attributes
    ----------
    f               : array
                      n x 1; observed flows; dependent variable; y
    n               : integer
                      number of observations
    c               : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cf              : function
                      cost function; used to transform cost variable
    ov              : array 
                      n x k; k attributes for each origin of n flows
    dv              : array 
                      n x k; k attributes for each destination of n flows
    params          : array
                      n*k, estimared beta coefficients
    yhat            : array
                      n*1, predicted value of y (i.e., fittedvalues)
    cov_params      : array
                      Variance covariance matrix (kxk) of betas
    std_err         : array
                      k*1, standard errors of betas
    pvalues         : array
                      k*1, two-tailed pvalues of parameters
    tvalues         : array
                      k*1, the tvalues of the standard errors
    deviance        : float
                      value of the deviance function evalued at params;
                      see family.py for distribution-specific deviance
    llf             : float
                      value of the loglikelihood function evalued at params;
                      see family.py for distribution-specific loglikelihoods
    aic             : float 
                      Akaike information criterion
    resid           : array
                      response residuals; defined as y-yhat
    results         : object
                      Full results from estimated model. May contain addtional
                      diagnostics
    Example
    -------
    TODO

    """
    def __init__(self, flows, o_vars, d_vars, cost,
            cost_func, constant=False, framework='GLM', SF=None, CD=None,
            Lag=None, Quasi=False):
        self.f = np.reshape(flows, (-1,1))
        self.ov = np.reshape(o_vars, (-1,1))
        self.dv = np.reshape(d_vars, (-1,1))
        self.c = np.reshape(cost, (-1,1))
        User.check_arrays(flows, o_vars, d_vars, cost)
        
        BaseGravity.__init__(self, self.f, self.c,
                cost_func, o_vars=self.ov, d_vars=self.dv, constant=constant,
                framework=framework, SF=SF, CD=CD, Lag=Lag, Quasi=Quasi)
        
    def local(self, loc_index, locs):
        """
        Calibrate local models for subsets of data from a single location to all
        other locations
        """
        results = {}
        covs = self.ov.shape[1] + self.dv.shape[1] + 1
        results['aic'] = []
        results['deviance'] = []
        for cov in range(covs):
            results['param' + str(cov)] = []
            results['pvalue' + str(cov)] = []
            results['tvalue' + str(cov)] = []
        for loc in np.unique(locs):
            subset = loc_index == loc
            f = self.reshape(self.f[subset])
            o_vars = self.reshape(self.ov[subset])
            d_vars = self.reshape(self.dv[subset])
            dij = self.reshape(self.c[subset])
            model = Gravity(f, o_vars, d_vars, dij, self.cf)
            results['aic'].append(model.aic)
            results['deviance'].append(model.deviance)
            for cov in range(covs):
                results['param' + str(cov)].append(model.params[cov])
                results['pvalue' + str(cov)].append(model.pvalues[cov])
                results['tvalue' + str(cov)].append(model.tvalues[cov])
        return results

class Production(BaseGravity):
    """
    Production-constrained (origin-constrained) gravity-type spatial interaction model
    
    Parameters
    ----------
    flows           : array of integers
                      n x 1; observed flows between O origins and D destinations
    origins         : array of strings
                      n x 1; unique identifiers of origins of n flows
    cost            : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cost_func       : string
                      functional form of the cost function; default is 'pow'
                      'exp' | 'pow'
    d_vars          : array (optional)
                      n x k; k attributes for each destination of n flows;
                      default is None

    Attributes
    ----------
    f               : array
                      n x 1; observed flows; dependent variable; y
    n               : integer
                      number of observations
    c               : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cf              : function
                      cost function; used to transform cost variable
    dv              : array 
                      n x k; k attributes for each destination of n flows
    params          : array
                      n*k, estimared beta coefficients
    yhat            : array
                      n*1, predicted value of y (i.e., fittedvalues)
    cov_params      : array
                      Variance covariance matrix (kxk) of betas
    std_err         : array
                      k*1, standard errors of betas
    pvalues         : array
                      k*1, two-tailed pvalues of parameters
    tvalues         : array
                      k*1, the tvalues of the standard errors
    deviance        : float
                      value of the deviance function evalued at params;
                      see family.py for distribution-specific deviance
    llf             : float
                      value of the loglikelihood function evalued at params;
                      see family.py for distribution-specific loglikelihoods
    aic             : float 
                      Akaike information criterion
    results         : object
                      Full results from estimated model. May contain addtional
                      diagnostics
    Example
    -------
    TODO

    """
    def __init__(self, flows, origins, d_vars, cost, cost_func, constant=False,
            framework='GLM', SF=None, CD=None, Lag=None, Quasi=False):
        self.f = self.reshape(flows)
        self.o = self.reshape(origins)
        self.dv = self.reshape(d_vars)
        self.c = self.reshape(cost)
        User.check_arr
        ays(flows, origins, d_vars, cost)
       
        BaseGravity.__init__(self, self.f, self.f, cost_func, d_vars=self.dv,
                origins=self.o, constant=constant, framework=framework,
                SF=SF, CD=CD, Lag=Lag, Quasi=Quasi)
    
    def local(self, locs=None):
        """
        Calibrate local models for subsets of data from a single location to all
        other locations
        """
        results = {}
        covs = self.dv.shape[1] + 1
        results['aic'] = []
        results['deviance'] = []
        for cov in range(covs):
            results['param' + str(cov)] = []
            results['pvalue' + str(cov)] = []
            results['tvalue' + str(cov)] = []
        if not locs:
        	locs = np.unique(self.o)
        for loc in np.unique(locs):
            subset = self.o == loc
            f = self.reshape(self.f[subset])
            o = self.reshape(self.o[subset])
            d_vars = self.reshape(self.dv[subset])
            dij = self.reshape(self.c[subset])
            model = Production(f, o, d_vars, dij, self.cf)
            results['aic'].append(model.aic)
            results['deviance'].append(model.deviance)
            for cov in range(covs):
                results['param' + str(cov)].append(model.params[cov])
                results['pvalue' + str(cov)].append(model.pvalues[cov])
                results['tvalue' + str(cov)].append(model.tvalues[cov])
        return results

class Attraction(BaseGravity):
    """
    Attraction-constrained (destination-constrained) gravity-type spatial interaction model
    
    Parameters
    ----------
    flows           : array of integers
                      n x 1; observed flows between O origins and D destinations
    destinations    : array of strings
                      n x 1; unique identifiers of destinations of n flows 
    cost            : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cost_func       : string
                      functional form of the cost function; default is 'pow'
                      'exp' | 'pow'
    o_vars          : array (optional)
                      n x k; k attributes for each origin of  n flows; default
                      is None

    Attributes
    ----------
    f               : array
                      n x 1; observed flows; dependent variable; y
    n               : integer
                      number of observations
    c               : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cf              : function
                      cost function; used to transform cost variable
    ov              : array
                      n x k; k attributes for each origin of n flows
    params          : array
                      n*k, estimared beta coefficients
    yhat            : array
                      n*1, predicted value of y (i.e., fittedvalues)
    cov_params      : array
                      Variance covariance matrix (kxk) of betas
    std_err         : array
                      k*1, standard errors of betas
    pvalues         : array
                      k*1, two-tailed pvalues of parameters
    tvalues         : array
                      k*1, the tvalues of the standard errors
    deviance        : float
                      value of the deviance function evalued at params;
                      see family.py for distribution-specific deviance
    llf             : float
                      value of the loglikelihood function evalued at params;
                      see family.py for distribution-specific loglikelihoods
    aic             : float 
                      Akaike information criterion
    results         : object
                      Full results from estimated model. May contain addtional
                      diagnostics
    Example
    -------
    TODO

    """
    def __init__(self, flows, destinations, o_vars, cost, cost_func,
            constant=False, framework='GLM', SF=None, CD=None, Lag=None,
            Quasi=False):
        self.f = np.reshape(flows, (-1,1))
        self.ov = np.reshape(o_vars, (-1,1))
        self.d = np.reshape(destinations, (-1,1))
        self.c = np.reshape(cost, (-1,1))
        User.check_arrays(flows, destinations, o_vars, cost)

        BaseGravity.__init__(self, self.f, self.c, cost_func, o_vars=self.ov,
                 destinations=self.d, constant=constant,
                 framework=framework, SF=SF, CD=CD, Lag=Lag, Quasi=Quasi)

    def local(self, locs=None):
        """
        Calibrate local models for subsets of data from a single location to all
        other locations
        """
        results = {}
        covs = self.ov.shape[1] + 1
        results['aic'] = []
        results['deviance'] = []
        for cov in range(covs):
            results['param' + str(cov)] = []
            results['pvalue' + str(cov)] = []
            results['tvalue' + str(cov)] = []
        if not locs:
        	locs = np.unique(self.d)
        for loc in np.unique(locs):
            subset = self.d == loc
            f = self.reshape(self.f[subset])
            d = self.reshape(self.d[subset])
            o_vars = self.reshape(self.ov[subset])
            dij = self.reshape(self.c[subset])
            model = Attraction(f, d, o_vars, dij, self.cf)
            results['aic'].append(model.aic)
            results['deviance'].append(model.deviance)
            for cov in range(covs):
                results['param' + str(cov)].append(model.params[cov])
                results['pvalue' + str(cov)].append(model.pvalues[cov])
                results['tvalue' + str(cov)].append(model.tvalues[cov])
        return results

class Doubly(BaseGravity):
    """
    Doubly-constrained gravity-type spatial interaction model
    
    Parameters
    ----------
    flows           : array of integers
                      n x 1; observed flows between O origins and D destinations
    origins         : array of strings
                      n x 1; unique identifiers of origins of n flows
    destinations    : array of strings
                      n x 1; unique identifiers of destinations of n flows 
    cost            : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cost_func       : string
                      functional form of the cost function; default is 'pow'
                      'exp' | 'pow'

    Attributes
    ----------
    f               : array
                      n x 1; observed flows; dependent variable; y
    n               : integer
                      number of observations
    c               : array 
                      n x 1; cost to overcome separation between each origin and
                      destination associated with a flow; typically distance or time
    cf              : function
                      cost function; used to transform cost variable
    params          : array
                      n*k, estimared beta coefficients
    yhat            : array
                      n*1, predicted value of y (i.e., fittedvalues)
    cov_params      : array
                      Variance covariance matrix (kxk) of betas
    std_err         : array
                      k*1, standard errors of betas
    pvalues         : array
                      k*1, two-tailed pvalues of parameters
    tvalues         : array
                      k*1, the tvalues of the standard errors
    deviance        : float
                      value of the deviance function evalued at params;
                      see family.py for distribution-specific deviance
    llf             : float
                      value of the loglikelihood function evalued at params;
                      see family.py for distribution-specific loglikelihoods
    aic             : float 
                      Akaike information criterion
    results         : object
                      Full results from estimated model. May contain addtional
                      diagnostics
    Example
    -------
    TODO

    """
    def __init__(self, flows, origins, destinations, cost, cost_func,
            constant=False, framework='GLM', SF=None, CD=None, Lag=None,
            Quasi=False):

        self.f = np.reshape(flows, (-1,1))
        self.o = np.reshape(origins, (-1,1))
        self.d = np.reshape(destinations, (-1,1))
        self.c = np.reshape(cost, (-1,1))
        User.check_arrays(flows, origins, destinations, cost)

        BaseGravity.__init__(self, self.f, self.c, cost_func, origins=self.o, 
                destinations=self.d, constant=constant,
                framework=framework, SF=SF, CD=CD, Lag=Lag, Quasi=Quasi)

    def local(self, locs=None, origins=True):
        """
        Calibrate local models for subsets of data from a single location to all
        other locations
        """
        raise NotImplementedError("Local models not possible for"
        " doubly-constrained model due to insufficient degrees of freedom.")
