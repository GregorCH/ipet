from scipy import stats

def mywilcoxon(firstdata, seconddata=None):
   if seconddata == None:
      return stats.wilcoxon(firstdata)
   else:
      return stats.wilcoxon(firstdata, seconddata)