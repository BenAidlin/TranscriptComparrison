"""
this module compares two lines
transforms them to vectors and finds euqlidian and cosine difference
finds number of grammer adjusments needed to transform line1 to line 2
"""

from sentence_transformers import SentenceTransformer ###this is a BERT module
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import euclidean_distances
from difflib import SequenceMatcher
from nltk.translate import bleu
from nltk.translate.bleu_score import SmoothingFunction
class CompTwoLines:
    bert_model = SentenceTransformer('bert-base-nli-mean-tokens') ### Static member
    def __init__(self, line1, line2):
        self.line1 = line1
        self.line2 = line2
    def setLines(self, line1, line2):
        self.line1=line1
        self.line2=line2
    def getEuqlidianDiff(self):
        #bert_model = SentenceTransformer('bert-base-nli-mean-tokens')
        arr = [self.line1, self.line2]
        veclist = CompTwoLines.bert_model.encode(arr)
        return (euclidean_distances(veclist)[1][0])
    def getCosineDiff(self):
        arr = [self.line1, self.line2]
        veclist = CompTwoLines.bert_model.encode(arr)
        return (cosine_similarity(veclist)[1][0])
    def countEditingChangesNeeded(self):
        s = SequenceMatcher(None, self.line1, self.line2)
        count=0
        for i in s.get_opcodes():
            if (i[0]=='delete'):
                count+=i[2] - i[1]
            if (i[0]=='insert'):
                count+=i[4]-i[3]
            if (i[0]=='replace'):
                count+=max(i[4]-i[3],i[2]-i[1])
        return count
    def calculateBLEU(self):
        return bleu([self.line1.split()],self.line2.split(), smoothing_function = SmoothingFunction().method7)

"""
usage example:
    
linex = "or this system is off by a full minute"
liney = "or this system is off"
c1 = CompTwoLines(linex, liney)
print(c1.calculateBLEU())
"""