from django.shortcuts import render
import tweepy
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import sys,tweepy,csv,re
from textblob import TextBlob
import matplotlib.pyplot as plt
import io
import urllib, base64
from django.http import Http404

consumerKey = 'InySQpmUKhCGO5gEnRi731q2C'
consumerSecret = 'VxfFPgTSFyXglZOYfV7TboPifsERpTcWjHHN0fONWq3A7DFBhi'
accessToken = '570234787-n8hfy2SCalAPeZiiuBoAqfSuDCsXWE1zO9AXrsxo'
accessTokenSecret = 'tm5C1Q7mQ3Ab6v2iVQ6c3uGBwkIaeQscz8whdeIN3MP9E'


# Create your views here.
def index(request):
    if request.method == 'POST':
        dataSearchText = request.POST['searchText']
        auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
        auth.set_access_token(accessToken, accessTokenSecret)
        api = tweepy.API(auth)
        tweets = api.search(dataSearchText, count=200)
        data = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['Tweets'])
        searchResult =  data.head(20)
        print(type(searchResult))
        print(list(searchResult))
        data.to_csv('data.csv')
        return render(request,'Uopbc/searchResult.html',{'dataSearchText':dataSearchText,'searchResult':searchResult,'rawdata':data})
    else:
        return render(request,'Uopbc/index.html')

def result(request):
    if request.method == 'POST':
        searchTerm = request.POST['nextData']
        data = pd.read_csv('data.csv')
        # print(data)
        sid = SentimentIntensityAnalyzer()

        listy = []

        for index, row in data.iterrows():
            ss = sid.polarity_scores(row["Tweets"])
            listy.append(ss)
        
        se =  pd.Series(listy)

        data["Polarity"] = se.values

        s = data["Tweets"]

        resultWithPolarity = data.head(100)
        print(list(resultWithPolarity))

        # return render(request,'Uopbc/index.html',{'searchResult':searchResult,'resultWithPolarity':resultWithPolarity})
        return render(request,'Uopbc/finalResult.html',{'resultWithPolarity':resultWithPolarity,'searchTerm':searchTerm})
    else:
        raise Http404("Poll does not exist")
        return render(request,'Uopbc/finalResult.html')


def pieResult(request):
    if request.method == 'POST':
        tweets = []
        tweetText = []
        searchTerm = request.POST['nextData']
        NoOfTerms = int(100)

        auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
        auth.set_access_token(accessToken, accessTokenSecret)
        api = tweepy.API(auth)

        # searching for tweets
        tweets = tweepy.Cursor(api.search, q=searchTerm, lang = "en").items(NoOfTerms)

        # Open/create a file to append data to
        csvFile = open('result.csv', 'a')

        
        csvWriter = csv.writer(csvFile)

        polarity = 0
        positive = 0
        wpositive = 0
        spositive = 0
        negative = 0
        wnegative = 0
        snegative = 0
        neutral = 0

         # iterating through tweets fetched
        for tweet in tweets:
            #Append to temp so that we can store in csv later. I use encode UTF-8
            tweetText.append(cleanTweet(tweet.text).encode('utf-8'))
            # print (tweet.text.translate(non_bmp_map))    #print tweet's text
            analysis = TextBlob(tweet.text)
            # print(analysis.sentiment)  # print tweet's polarity
            polarity += analysis.sentiment.polarity  # adding up polarities to find the average later

            if (analysis.sentiment.polarity == 0):  # adding reaction of how people are reacting to find average later
                neutral += 1
            elif (analysis.sentiment.polarity > 0 and analysis.sentiment.polarity <= 0.3):
                wpositive += 1
            elif (analysis.sentiment.polarity > 0.3 and analysis.sentiment.polarity <= 0.6):
                positive += 1
            elif (analysis.sentiment.polarity > 0.6 and analysis.sentiment.polarity <= 1):
                spositive += 1
            elif (analysis.sentiment.polarity > -0.3 and analysis.sentiment.polarity <= 0):
                wnegative += 1
            elif (analysis.sentiment.polarity > -0.6 and analysis.sentiment.polarity <= -0.3):
                negative += 1
            elif (analysis.sentiment.polarity > -1 and analysis.sentiment.polarity <= -0.6):
                snegative += 1


     
        csvWriter.writerow(tweetText)
        csvFile.close()

        # finding average of how people are reacting
        positive = percentage(positive, NoOfTerms)
        wpositive = percentage(wpositive, NoOfTerms)
        spositive = percentage(spositive, NoOfTerms)
        negative = percentage(negative, NoOfTerms)
        wnegative = percentage(wnegative, NoOfTerms)
        snegative = percentage(snegative, NoOfTerms)
        neutral = percentage(neutral, NoOfTerms)

        polarity = polarity / NoOfTerms
        generalReport = ''
        if (polarity == 0):
            generalReport = 'Neutral'
            print("Neutral")
        elif (polarity > 0 and polarity <= 0.3):
            generalReport = 'Weakly Positive'
            print("Weakly Positive")
        elif (polarity > 0.3 and polarity <= 0.6):
            generalReport = 'Positive'
            print("Positive")
        elif (polarity > 0.6 and polarity <= 1):
            generalReport = 'Strongly Positive'
            print("Strongly Positive")
        elif (polarity > -0.3 and polarity <= 0):
            generalReport = 'Weakly Negative'
            print("Weakly Negative")
        elif (polarity > -0.6 and polarity <= -0.3):
            generalReport = 'Negative'
            print("Negative")
        elif (polarity > -1 and polarity <= -0.6):
            generalReport = 'Strongly Negative'
            print("Strongly Negative")

        plt2 = plotPieChart(positive, wpositive, spositive, negative, wnegative, snegative, neutral, searchTerm, NoOfTerms)
        fig = plt2.gcf()
        buf  = io.BytesIO()
        fig.savefig(buf,format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = urllib.parse.quote(string)
        return render(request,'Uopbc/pieFinalResult.html',{'searchTerm':searchTerm,'NoOfTerms':NoOfTerms,'generalReport':generalReport,'uri':uri,'positive':positive,'wpositive': wpositive, 'spositive':spositive, 'negative':negative,'wnegative': wnegative, 'snegative':snegative, 'neutral':neutral})
    else:
        raise Http404("Poll does not exist")
        return render(request,'Uopbc/pieFinalResult.html')

def cleanTweet(tweet):
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) | (\w +:\ / \ / \S +)", " ", tweet).split())


# function to calculate percentage
def percentage(part, whole):
    temp = 100 * float(part) / float(whole)
    return format(temp, '.2f')

def plotPieChart(positive, wpositive, spositive, negative, wnegative, snegative, neutral, searchTerm, noOfSearchTerms):
    labels = ['Positive [' + str(positive) + '%]', 'Weakly Positive [' + str(wpositive) + '%]','Strongly Positive [' + str(spositive) + '%]', 'Neutral [' + str(neutral) + '%]',
                  'Negative [' + str(negative) + '%]', 'Weakly Negative [' + str(wnegative) + '%]', 'Strongly Negative [' + str(snegative) + '%]']
    sizes = [positive, wpositive, spositive, neutral, negative, wnegative, snegative]
    colors = ['yellowgreen','lightgreen','darkgreen', 'gold', 'red','lightsalmon','darkred']
    patches, texts = plt.pie(sizes, colors=colors, startangle=90)
    plt.legend(patches, labels, loc="best")
    plt.title('people are reacting on ' + searchTerm + ' by analyzing ' + str(noOfSearchTerms) + ' Tweets.')
    plt.axis('equal')
    plt.tight_layout()
    return plt

