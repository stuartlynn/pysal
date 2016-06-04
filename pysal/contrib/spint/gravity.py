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

import numpy as np
from scipy import sparse as sp
import statsmodels.api as sm
from statsmodels.api import families 
from statsmodels.tools.tools import categorical
from sparse_categorical import spcategorical
from pysal.spreg import user_output as User
from count_base import CountModel

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
    params          : array
                      estimated parameters
    se              : array
                      standard errors associated with estimated parameters
    t_stats         : array
                      t-statistics associated with estimated parameters for
                      hypothesis testing
    fitted          : array
                      n x 1; flow values produced by calibrated model
    fit_stats       : dict{"statistic name": statistic value}
    
    Example
    -------
    TODO

    """
    def __init__(self, flows, cost, cost_func='pow', o_vars=None, d_vars=None,
            origins=None, destinations=None, constant=False, framework='SM_GLM'):
        n = User.check_arrays(flows, cost)
        User.check_y(flows, n)
        self.n = n
        self.f = flows
        self.c = cost
        self.ov = o_vars
        self.dv = d_vars

        if cost_func.lower() == 'pow':
            self.cf = np.log
        elif cost_func.lower() == 'exp':
            self.cf = lambda x: x*1.0
        else:
            raise ValueError('cost_func must either be "exp" or "power"')

        y = np.reshape(self.f, (-1,1))
        
        #X = np.empty((self.n, 0))
        X = sp.csr_matrix((self.n, 1))

        if isinstance(self, Attraction) | isinstance(self, Doubly):
            #d_dummies = categorical(destinations.flatten().astype(str), drop=True)
            d_dummies = spcategorical(destinations.flatten().astype(str)) 
            #X = np.hstack((X, d_dummies))
            X = sp.hstack((X, d_dummies))
        if isinstance(self, Production) | isinstance(self, Doubly):
            #o_dummies = categorical(origins.flatten().astype(str), drop=True)
            o_dummies = spcategorical(origins.flatten().astype(str)) 
            #X = np.hstack((X, o_dummies))
            X = sp.hstack((X, o_dummies))
        if isinstance(self, Doubly):
            X = sp.csr_matrix(X)
            X = X[:,1:]
        if self.ov is not None:
            #X = np.hstack((X, np.log(np.reshape(self.ov, (-1,1)))))
            ov = sp.csr_matrix(np.log(np.reshape(self.ov, ((-1,1)))))
            X = sp.hstack((X, ov))
        if self.dv is not None:
            #X = np.hstack((X, np.log(np.reshape(self.dv, (-1,1)))))
            dv = sp.csr_matrix(np.log(np.reshape(self.dv, ((-1,1)))))
            X = sp.hstack((X, dv))
        #X = np.hstack((X, self.cf(np.reshape(self.c, (-1,1)))))
        c = sp.csr_matrix(self.cf(np.reshape(self.c, (-1,1))))
        X = sp.hstack((X, c))
        X = sp.csr_matrix(X)
        X = X[:,1:]
        
        CountModel.__init__(self, y, X, constant=constant)
        
        if (framework.lower() == 'sm_glm'):
            self.fit()
        elif (framework.lower() == 'glm'):
            self.fit(framework='glm')
        

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
                      estimated parameters
    se              : array
                      standard errors associated with estimated parameters
    t_stats         : array
                      t-statistics associated with estimated parameters for
                      hypothesis testing
    fitted          : array
                      n x 1; flow values produced by calibrated model
    fit_stats       : dict{"statistic name": statistic value}
    
    Example
    -------
    TODO

    """
    def __init__(self, flows, o_vars, d_vars, cost,
            cost_func, constant=False, framework='SM_GLM'):
        flows = np.reshape(flows, (-1,1))
        o_vars = np.reshape(o_vars, (-1,1))
        d_vars = np.reshape(d_vars, (-1,1))
        cost = np.reshape(cost, (-1,1))
        User.check_arrays(flows, o_vars, d_vars, cost)
        
        BaseGravity.__init__(self, flows, cost,
                cost_func, o_vars=o_vars, d_vars=d_vars, constant=constant,
                framework=framework)

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
                      estimated parameters
    se              : array
                      standard errors associated with estimated parameters
    t_stats         : array
                      t-statistics associated with estimated parameters for
                      hypothesis testing
    fitted          : array
                      n x 1; flow values produced by calibrated model
    fit_stats       : dict{"statistic name": statistic value}

    Example
    -------
    TODO

    """
    def __init__(self, flows, origins, d_vars, cost, cost_func, constant=False,
            framework='SF_GLM'):
        flows = np.reshape(flows, (-1,1))
        origins = np.reshape(origins, (-1,1))
        d_vars = np.reshape(d_vars, (-1,1))
        cost = np.reshape(cost, (-1,1))
        User.check_arrays(flows, origins, d_vars, cost)
       
        BaseGravity.__init__(self, flows, cost, cost_func, d_vars=d_vars,
                origins=origins, constant=constant, framework=framework)
        
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
                      estimated parameters
    se              : array
                      standard errors associated with estimated parameters
    t_stats         : array
                      t-statistics associated with estimated parameters for
                      hypothesis testing
    fitted          : array
                      n x 1; flow values produced by calibrated model
    fit_stats       : dict{"statistic name": statistic value}

    Example
    -------
    TODO

    """
    def __init__(self, flows, destinations, o_vars, cost, cost_func,
            constant=False, framework='SM_GLM'):
        flows = np.reshape(flows, (-1,1))
        o_vars = np.reshape(o_vars, (-1,1))
        destinations = np.reshape(destinations, (-1,1))
        cost = np.reshape(cost, (-1,1))
        User.check_arrays(flows, destinations, o_vars, cost)

        BaseGravity.__init__(self, flows, cost, cost_func, o_vars=o_vars,
                 destinations=destinations, constant=constant, framework=framework)

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
                      estimated parameters
    se              : array
                      standard errors associated with estimated parameters
    t_stats         : array
                      t-statistics associated with estimated parameters for
                      hypothesis testing
    fitted          : array
                      n x 1; flow values produced by calibrated model
    fit_stats       : dict{"statistic name": statistic value}

    Example
    -------
    TODO

    """
    def __init__(self, flows, origins, destinations, cost, cost_func,
            constant=False, framework='SM_GLM'):
        flows = np.reshape(flows, (-1,1))
        origins = np.reshape(origins, (-1,1))
        destinations = np.reshape(destinations, (-1,1))
        cost = np.reshape(cost, (-1,1))
        User.check_arrays(flows, origins, destinations, cost)

        BaseGravity.__init__(self, flows, cost, cost_func, origins=origins, 
                destinations=destinations, constant=constant, framework=framework)
