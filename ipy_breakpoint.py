#  This is for ipython interactive
#  - you can, for example, place this in
#    ~/.ipython/profile_default/startup

def breakpoint_(condition=True):
    '''
    in ipython:
    - breakpoint_() <= break always
    - breakpoint_(False) <= never break
    - breakpoint_(condition) <= break if True
    '''
    # import here, to limit the imported names
    # to this function's namespace
    from sys import _getframe
    from IPython.terminal import debugger
    if condition:
        debugger.set_trace(_getframe().f_back)
        return debugger
