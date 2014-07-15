from scipy import stats

def mywilcoxon(firstdata, seconddata):
   return stats.wilcoxon(firstdata, seconddata)