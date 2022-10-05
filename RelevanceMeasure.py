import re
import nltk
from backEnd.cfeHome.prodacut.models import Prod

class RelevanceMeasure :

    totalWordsCount = 0
    totalWordCoOccurencesCount = 0
    uod_table = "uod_titles"	
    minWordCountLimit = 0
    keywordlist = []
    minCoOccurCountLimit = 0
    dataList = []
    FilterWords_file_url="any url "
    uod_table ="prod"
    fileAddress = "any url"
    resultFileAddress = "any url"
    
    
    def main():
     global FilterWords_file_url   
     global minWordCountLimit
     global minCoOccurCountLimit
     global uod_table
     global fileAddress
     global rm
     global dataList
     global totalWordCoOccurencesCount
     global totalWordsCount
     global words_2b_filtered
     rm =RelevanceMeasure()
     rm.getTotalWordCountFromDB()
     rm.getTotalWordCoOccurencesFromDB()
     rm.loadFilterWords()
     rm.loadDataFromFile(fileAddress)
     global results 
     rm.keyWordsList.add("stc")
     rm.keyWordsList.add("saudi")
    for x in  range(0,  14) :
      text = rm.dataList[x]
      wordsList = rm.text2UniqueWords(dataList[x])
      uod_Net_Weight = rm.calcUoD_NetworkWeight(wordsList, rm.keyWordsList )
      keyWordsPresenceWeight = 0
      relevance = (keyWordsPresenceWeight + (uod_Net_Weight))		
      results += text + "," + keyWordsPresenceWeight + "," +uod_Net_Weight + "," + relevance +"\n"				

    try:
       f = open(resultFileAddress, "a")
       f.write(results)
       f.close()
    except Exception as e:
        raise e 	



    def getTotalWordCountFromDB():
        
        try:
         wordCountQueryResultSet =  Prod.objects.raw("Select Word, WordCount from " + uod_table + " GROUP BY Word ;")
         for x in wordCountQueryResultSet:
          if x.WordCount >= minWordCountLimit :
            totalWordsCount += x.WordCount
         cowordCountQueryResultSet =  Prod.objects.raw('Select DISTINCT(CoWord), CoWordCount from ' +uod_table +	' WHERE CoWord NOT IN (SELECT DISTINCT(Word) from uod_titles);') 
         for x in cowordCountQueryResultSet:
          if x.CoWordCount >= minWordCountLimit :
            totalWordsCount += x.CoWordCount   
        except Exception as e:
            raise e 
        
        return totalWordsCount   

    def getTotalWordCoOccurencesFromDB():
        try:
          wordCountQueryResultSet  =  Prod.objects.raw("Select SUM(CoOccurenceCount) as sucw from " + uod_table )
          for x in wordCountQueryResultSet :
            if x.sucw >= minCoOccurCountLimit:
             totalWordCoOccurencesCount =  x.sucw        
        except Exception as e:
            raise e 
        
        return totalWordCoOccurencesCount        

    def loadFilterWords():
        words_2b_filtered = ""
        try:
          file = open(FilterWords_file_url, "r")
          for line in file:
           line= file.readline()
           words_2b_filtered+= line
        except Exception as e:
            raise e 
     
    def loadDataFromFile(file_url):

        try:
          file = open(file_url, "r")
          for line in file:
           line= file.readline()
           dataList.add(line)
        except Exception as e:
            raise e 

    
    def text2UniqueWords ( self,text) :
        listOfWords=[]
        text=re.sub(r'[\W_]+', '', text) # remove non-alphanumeric characters 
        st =  nltk.sent_tokenize(text)
        for x in   range(0, len(st) -1):
            strWord = st[x+1].lower().strip()
            if (self.isfilterWord(strWord)):
             continue
            for i in   range(0, len(listOfWords) -1):
              if(listOfWords[i].lower()==strWord):
                 alreadyListed = True
            if (alreadyListed==False and len(strWord) > 1 ):
               listOfWords.append(strWord)   
        
        return listOfWords         

    
    def  isfilterWord( self,strWord):
       global skipWord 
       st = nltk.sent_tokenize(words_2b_filtered, ",")
       for x in  range(0, len(st) -1) :
        strFilterWord = st[x+1].lower()
        if(strFilterWord==strWord.lower()):
            skipWord=True
            break
       return skipWord 
  

    def calcUoD_NetworkWeight(self,wordsList,keyWordsList):
     uod_Net_Weight = 0.0
     RelationshipWeight = 0.0
     for i in range(0,len(keyWordsList)-1):
        keyWord = keyWordsList[i]
        for j in range(0, len(wordsList-1)):
         testWord = wordsList[j]
         if ( testWord in keyWordsList  ):
            continue
         RelationshipWeight += self.calcRelationshipWeight(keyWord, testWord)
     uod_Net_Weight += RelationshipWeight
     return uod_Net_Weight    


    def  calcRelationshipWeight(self,keyWord,testWord):
      coWordsList1 = self.getCoWordsList(keyWord)
      coWordsList2 = self.getCoWordsList(testWord)
      commonWordsList =[]
      for x in range(0, len(coWordsList1)-1):
        for y in range(0, len(coWordsList2)-1) :
            if(coWordsList1[x].lower()==coWordsList2[y].lower()):
                commonWordsList.append(coWordsList1[x])
      if (commonWordsList.size() < 1):
        return 0  
      relationshipWeightage = 0.0   
      for x in   range(0, len(commonWordsList)-1):
        f = self.calCoOccurenceWeight(keyWord, commonWordsList[x])+self.calCoOccurenceWeight(testWord, commonWordsList[x])
        relationshipWeightage += f
        
      return relationshipWeightage  	
      	       
    
    def getCoWordsList(self,word):    
     coWordsList =[]
     coWordsQueryResultSet=Prod.objects.raw("Select CoWord from " + uod_table + " WHERE Word = '"+word+"'")
     for x in coWordsQueryResultSet:
        coWord = x.CoWord
        if(coWord in self.keyWordsList):
            continue
        coWordsList.append(coWord)

     coWordsQueryResultSet=Prod.objects.raw("Select Word from " + uod_table + " WHERE CoWord = '"+word+"'") 
     for x in coWordsQueryResultSet:
        Word = x.Word
        if(Word in self.keyWordsList):
            continue
        coWordsList.append(coWord)    

     return coWordsList

    def calCoOccurenceWeight(self, word,coWord) :
      coOccurenceWeight = 0.0	
      coOccurrenceCount = 0
      wordCount = 0 
      coWordCount = 0
      try:
       coOccurenceCountQueryResultSet=Prod.objects.raw(" Select CoOccurenceCount from " + uod_table +
					" WHERE (Word='"+word+"' AND CoWord='"+coWord+"')" +
					" OR (CoWord='"+word+"' AND Word='"+coWord+"')") 
       if (len(coOccurenceCountQueryResultSet)==1):          
         coOccurrenceCount = coOccurenceCountQueryResultSet[0].CoOccurenceCount  
         wordCount = self.getWordCountFromDB(word)
         coWordCount =self.getWordCountFromDB(coWord)
         
		# L*(w1+w2)  
         w1_plus_w2 = ((wordCount*1.0)/(totalWordsCount*1.0))+((coWordCount*1.0)/(totalWordsCount*1.0))
         L = (coOccurrenceCount*1.0/totalWordCoOccurencesCount*1.0)
         coOccurenceWeight = (w1_plus_w2)*L		    
      except Exception as e:
        raise e 
      return coOccurenceWeight


    def getWordCountFromDB(self,word):
      wordCount = 0
      try:
       wordCountQueryResultSet=Prod.objects.raw("Select WordCount from " + uod_table + " WHERE Word='"+word+"'") 
       if (len(wordCountQueryResultSet)==1):          
         wordCount = wordCountQueryResultSet[0].WordCount  
       else :
        wordCountQueryResultSet=Prod.objects.raw("Select CoWordCount from " + uod_table + " WHERE CoWord='"+word+"'") 
        if (len(wordCountQueryResultSet)==1):          
         wordCount = wordCountQueryResultSet[0].CoWordCount  
      except Exception as e:
        raise e 
      return wordCount  
        
