try:
  import nuke
  def debug(x):
    nuke.debug(str(x))
    return x
except:
  def debug(x):
    print(x)
    return x
