# SOTD Decider
Script to quantitatively determine my Song of the Day using the notion of TF-IDF scores. 

#### Background
I have a little tradition of posting my "song of the day" (SOTD from here on) on a private Instagram story each evening alongside a summary of my day (a therapeutic exercise, kind of). My classification of a song as my SOTD is generally subjective, but it tends to be the most *repeated* song I listened to in the given day that is also the most *unique*. As in, it should be a song that I listened to a lot in the given day, that I didn't listen to as much in other days. I realized that my mental model of deciding on a SOTD can be likened to a TF-IDF score, where in this application each song is equivalent to a term/word, and each day is equivalent to a document. 

I am aware that this is a completely trivial task (in practicality and in difficulty), but the idea came up and I just had to implement it. I think it would be fun to see how my mental TF-IDF model aligns with actual scores.

#### TF-IDF
Term Frequency-Inverse Document Frequency (TF-IDF) is a statistical metric that evaluates how "important" a word is to a document relative to a collection of documents. Each *word* in each document is given a TF-IDF score, which is defined as the product of term frequency (how many times the word appears in the document over the total number of words in the document) and inverse document frequency (a measure of how unique the word is within the corpus of documents).

The computation of the TF-IDF score for each word $t$ in some document $D$ within a corpus is given as follows: 

$$\textnormal{TF}(t, D) = \frac {\textnormal{num. of times word \textit t appears in \textit D}} {\textnormal{total num. of words in \textit D}}$$

$$\textnormal{IDF}(t) = \textnormal{log}(\frac {\textnormal{num. of documents in corpus}}{\textnormal{num. of documents in corpus that contain word \textit t}})$$

$$\textnormal{TF-IDF}(t, D) = \textnormal{TF}(t, D) \times \textnormal{IDF}(t)$$

So, imagine you have a corpus of text documents. By running TF-IDF on this corpus, you could obtain a numerical representation (of importance) of all the text within the corpus - as in, you could end up with a matrix where each row represents a document, and each column represents a particular word within a particular document. The value in each cell then represents the importance of a particular word in a document relative to the entire corpus (note, however, that days are obviously temporal, so the matrix representation does not hold here). 

The TF-IDF score will be high for a given word if that word is "important" to a given document. "Important" here means that the word is both frequent in the document (measured by TF) and unique to the document relative to all documents in the corpus (measured by IDF).

TF-IDF is a commonly-used technique in feature generation for natural language processing applications. In this case, however, I'd like to generalize its use (or really, the notion of it) to measure the importance of a song (analogous to a term) to my day (document) relative to many days (corpus). 

#### Methodology
Implementation is straightforward. I built a class `SOTDecider` that takes in a time range from which listening history will be pulled (serving as the corpus), computes TF-IDF scores for each song from the current day, and ultimately prints a table containing each song with alongside its score. The possible options for time range are `["this week", "last X days"]`, where `X` in `"last X days"` is any valid positive integer. 

The TF-IDF scores are computed in the standard way, with a slight modification. As the time ranges are fairly short, IDF (and hence TF-IDF) will be 0 if I listened to a given song each day in the range. I'd like to place higher priority on the repetitiveness of a given track, so `(0.3 * TF)` is added to the final TF-IDF score.

$$\textnormal{TF}(s, D) = \frac {\textnormal{num. of times song \textit s was played in day \textit D}} {\textnormal{total number of streams in \textit D}}$$

$$\textnormal{IDF}(s) = \textnormal{log}(\frac {\textnormal{num. of days in date range}}{\textnormal{num. of days in range during which song \textit s was played}})$$

$$\textnormal{TF-IDF}(s, D) = (\textnormal{TF}(s, D) \times \textnormal{IDF}(s)) + (0.3 \times \textnormal{TF}(s, D))$$