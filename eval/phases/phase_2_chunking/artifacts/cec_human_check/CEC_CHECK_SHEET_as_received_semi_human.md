# CEC Human Check (30 cases)

For each case, read the question, the reference answer(s) and the gold evidence, then the **context**.
Decide: **does the context contain enough information for a reader to answer the question?**
Mark exactly one box. Use UNSURE only if you really cannot decide. Do not open `cec_check_key.json`.

## CEC-01

**Question:** Do they remove seasonality from the time series?

**Reference answer(s):** No

<details><summary>Gold evidence</summary>

> Data Pre-Processing
> Stock prices data collected is not complete understandably because of weekends and public holidays when the stock market does not function. The missing data is approximated using a simple technique by Goel BIBREF17 . Stock data usually follows a concave function. So, if the stock value on a day is x and the next value present is y with some missing in between. The first missing value is approximated to be (y+x)/2 and the same method is followed to fill all the gaps.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Chen, K., Corrado, G. and Dean, J. (2013) Distributed Representations of Words and Phrases and Their Composi- tionality. Proceedings of Neural Information Processing Systems, Lake Tahoe, December 2013, 3111-3119 [20] Mark Hall, Eibe Frank, Geoffrey Holmes, Bernhard Pfahringer, Peter Reutemann, Ian H. Witten (2009); The WEKA Data Mining Software: An Update; SIGKDD Explorations, Volume 11, Issue 1. [21] http://brnrd.me/social-sentiment-sentiment-analysis/ [22] http://stocktwits.com/home [23] https://in.ﬁnance.yahoo.com/ Fig. 1: Flow Chart of the proposed analysis TABLE I: Sample tweets sentiment labeling by the model I’m really excited that today is my ﬁrst day at @Microsoft as a Technical Evangelist 1 Ultrabooks in the mainstream ( AAPLiPadProincontention ) | MSFT 1 About the Surface team, it’s one of the most secret team at @Microsoft , except VPs, no one knows what they do, so don’t expect leaks ;) 1 We broke all your devices, we force you to update whenever we want, and we spy on you all the time. Happy Anniversary!” - @microsoft 0 My grandfather, a depression era company man, hated that $ MSFT didn’t pay dividends (90s). I never could explain ”new” idea of growth/cash. 2 Thanks @Microsoft , delivered my Surface Pro 3 power plug to a newsagents 20 miles from my home with no notiﬁcation. 0 10 swift lessons. My post on @SwiftKey @Microsoft @georgewhitehead @OctopusVentures @IndexVentures @Accel 0 @Microsoft Acquires MinecraftEdu, Tailored for Schools http:// nyti.ms/1U9a1oV (via: @nytimesbusiness 0 My surface’s touchscreen stopped working... I have homework... @Microsoft expand your customer service hours please 0 MSFT trailing revenues are declining since 2015, net income is up thanks to higher margins 2 TABLE II: Sentiment Analysis Results Machine Learning Algorithm Word2vec N-gram Accuracy Precision Recall F-Measure Accuracy Precision Recall F-Measure Random Forest 70.18% 0.711 0.702 0.690 70.49% 0.719 0.705 0.694 Logistic Regression 62.42% 0.621 0.624 0.621 57.14% 0.580 0.571 0.574

---

of the ACM International Conference on Web Intelligence, pp. 492-499 (2010) [7] Ruiz, E. J., Hristidis, V., Castillo, C., Gionis, A., Jaimes, A.: Correlating ﬁnancial time se-ries with micro-blogging activity. In: Proceedings of the ﬁfth ACM international confer-ence on Web search and data mining, pp. 513-522 (2012) [8] Bordino, I., Battiston, S., Caldarelli, G., Cristelli, M., Ukkonen, A., Weber, I.: Web search queries can predict stock market volumes. PLoS ONE 7(7), e40014 (2011) [9] Gilbert, E., Karahalios, K.: Widespread Worry and the Stock Market. In: Proceedings of the Fourth International AAAI Conference on Weblogs and Social Media, pp.58-65 (2010) [10] Bollen, J., Mao, H., Zeng, X.: Twitter mood predicts the stock market. Journal of Compu-tational Science, 2(1), 1-8 (2011) [11] Aramaki, Eiji, Sachiko Maskawa, and Mizuki Morita. ”Twitter catches the ﬂu: detecting inﬂuenza epidemics using Twitter.” Proceedings of the conference on empirical methods in natural language processing. Association for Computational Linguistics, 2011. [12] R. Chen and M. Lazer, Sentiment Analysis of Twitter Feeds for the Prediction of Stock Market Movement, Cs 229, pp. 15, 2011. [13] L. Zhang, Sentiment Analysis on Twitter with Stock Price and Signiﬁ- cant Keyword Correlation, pp. 130, 2013. [14] Dickinson, Brian, and Wei Hu. ”Sentiment analysis of investor opinions on twitter.” Social Networking 4.03 (2015): 62. [15] Bing, Li, Keith CC Chan, and Carol Ou. ”Public sentiment analysis in Twitter data for prediction of a company’s stock price movements.” e- Business Engineering (ICEBE), 2014 IEEE 11th International Conference on. IEEE, 2014. [16] https://dev.twitter.com/overview/api [17] Mittal, Anshul, and Arpit Goel. ”Stock prediction using twitter sentiment analysis.” Standford University, CS229 (2011 http://cs229. stanford. edu/proj2011/GoelMittal- StockMarketPredictionUsingTwitterSentimentAnalysis. pdf) (2012). [18] Agarwal, Apoorv, et al. ”Sentiment analysis of twitter data.” Proceedings of the workshop on languages in social media. Association for Compu- tational Linguistics, 2011. [19] Tomas, M., Sutskever, I.,

---

[16]. Twitter4J is a java application which helps us to extract tweets from twitter. The tweets were collected using Twitter API and ﬁltered using keywords like $ MSFT, # Microsoft, #Windows etc. Not only the opinion of public about the company’s stock but also the opinions about products and services offered by the company would have a signiﬁcant impact and are worth studying. Based on this principle, the keywords used for ﬁltering are devised with extensive care and tweets are extracted in such a way that they represent the exact emotions of public about Microsoft over a period of time. The news on twitter about Microsoft and tweets regarding the product releases were also included. Stock opening and closing prices of Microsoft from August 31st, 2015 to August 25th, 2016 are obtained from Yahoo! Finance [23]. B. Data Pre-Processing Stock prices data collected is not complete understandably because of weekends and public holidays when the stock market does not function. The missing data is approximated using a simple technique by Goel [17]. Stock data usually follows a concave function. So, if the stock value on a day is x and the next value present is y with some missing in between. The ﬁrst missing value is approximated to be (y+x)/2 and the same method is followed to ﬁll all the gaps. Tweets consists of many acronyms, emoticons and unneces- sary data like pictures and URL’s. So tweets are preprocessed to represent correct emotions of public. For preprocessing of tweets we employed three stages of ﬁltering: Tokenization, Stopwords removal and regex matching for removing special characters. based on the space and irrelevant symbols like emoticons are removed. We form a list of individual words for each tweet. emotion are called Stopwords. After splitting a tweet, words like a,is, the, with etc.

---

stock price. Our speculation is well supported by the results achieved and seems to have a promising future in research. In this work, we have considered only twitter data for analyzing people’s sentiment which may be biased because not all the people who trade in stocks share their opinions on twitter. Stocktwits [22] is a ﬁnancial communication platform designed solely for sharing ideas and insights of investors, entrepreneurs and traders. The current study can be extended by incorporating stocktwits data. In addition to this, data from news can also be included for an exhaustive public opinion collection. While training the sentiment analyzer, 3,216 tweets are used which is comparatively a less number to train a sentiment analyzer. In future, we look forward to human annotate more than 10,000 tweets and train the classiﬁers. With increasing size of training datasets, the models tend to perform better. A CKNOWLEDGMENT The authors would like to thank the students of IIT Bhubaneswar who contributed to the human annotation of tweets. [1] Qian, Bo, Rasheed, Khaled, Stock market prediction with multi- ple classiﬁers, Applied Intelligence 26 (February (1)) (2007) 2533, http://dx.doi.org/10.1007/s10489-006-0001-7. [2] E.F. Fama, The behavior of stock-market prices, The Journal of Business 38 (1) (1965) 34105, http://dx.doi.org/10.2307/2350752 [3] J. Leskovec, L. Adamic and B. Huberman. The dynamics of viral marketing. In Proceedings of the 7th ACM Conference on Electronic Commerce. 2006 [4] B. Jansen, M. Zhang, K. Sobel, and A. Chowdury. Twitter power: Tweets as electronic word of mouth. Journal of the American Society for Information Science and Technology. 2009. [5] A. Pak and P. Paroubek, Twitter as a corpus for sentiment analysis and opinion mining, in Proceedings of the Seventh International Conference on Language Resources and Evaluation, 2010, pp. 13201326 [6] Asur, S., Huberman, B.A.: Predicting the Future with Social Media. In: Proceedings
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Pre-processing section is present: only gap-filling of missing days, no seasonality removal mentioned -> 'No' is answerable.

## CEC-02

**Question:** what are the pivot-based baselines?

**Reference answer(s):** pivoting | pivoting$_{\rm m}$ ‖ firstly translates a source language into the pivot language which is later translated to the target language

<details><summary>Gold evidence</summary>

> Table TABREF19 and TABREF26 report zero-shot results on Europarl and Multi-UN evaluation sets, respectively. We compare our approaches with related approaches of pivoting, multilingual NMT (MNMT) BIBREF19, and cross-lingual transfer without pretraining BIBREF16. The results show that our approaches consistently outperform other approaches across languages and datasets, especially surpass pivoting, which is a strong baseline in the zero-shot scenario that multilingual NMT systems often fail to beat BIBREF19, BIBREF20, BIBREF23. Pivoting translates source to pivot then to target in two steps, causing inefficient translation process. Our approaches use one encoder-decoder model to translate between any zero-shot directions, which is more efficient than pivoting. Regarding the comparison between transfer approaches, our cross-lingual pretraining based transfer outperforms transfer method that does not use pretraining by a large margin.
> Although it is challenging for one model to translate all zero-shot directions between multiple distant language pairs of MultiUN, MLM+BRLM-SA still achieves better performances on Es $\rightarrow $ Ar and Es $\rightarrow $ Ru than strong pivoting$_{\rm m}$, which uses MNMT to translate source to pivot then to target in two separate steps with each step receiving supervised signal of parallel corpora. Our approaches surpass pivoting$_{\rm m}$ in all zero-shot directions by adding back translation BIBREF33 to generate pseudo parallel sentences for all zero-shot directions based on our pretrained models such as MLM+BRLM-SA, and further training our universal encoder-decoder model with these pseudo data. BIBREF22 gu2019improved introduces back translation into MNMT, while we adopt it in our transfer approaches. Finally, our best MLM+BRLM-SA with back translation outperforms pivoting$_{\rm m}$ by 2.4 BLEU points averagely, and outperforms MNMT BIBREF22 by 4.6 BLEU points averagely. Again, in supervised translation directions, MLM+BRLM-SA with back translation also achieves better performance than the original supervised Transformer.
> We use traditional transfer learning, pivot-based method and multilingual NMT as our baselines. For the fair comparison, the Transformer-big model with 1024 embedding/hidden units, 4096 feed-forward filter size, 6 layers and 8 heads per layer is adopted for all translation models in our experiments. We set the batch size to 2400 per batch and limit sentence length to 100 BPE tokens. We set the $\text{attn}\_\text{drop}=0$ (a dropout rate on each attention head), which is favorable to the zero-shot translation and has no effect on supervised translation directions BIBREF22. For the model initialization, we use Facebook's cross-lingual pretrained models released by XLM to initialize the encoder part, and the rest parameters are initialized with xavier uniform. We employ the Adam optimizer with $\text{lr}=0.0001$, $t_{\text{warm}\_\text{up}}=4000$ and $\text{dropout}=0.1$. At decoding time, we generate greedily with length penalty $\alpha =1.0$.
> Pivot-based Method is a common strategy to obtain a source$\rightarrow $target model by introducing a pivot language. This approach is further divided into pivoting and pivot-synthetic. While the former firstly translates a source language into the pivot language which is later translated to the target language BIBREF4, BIBREF5, BIBREF12, the latter trains a source$\rightarrow $target model with pseudo data generated from source-pivot or pivot-target parallel data BIBREF13, BIBREF14. Although the pivot-based methods can achieve not bad performance, it always falls into a computation-expensive and parameter-vast dilemma of quadratic growth in the number of source languages, and suffers from the error propagation problem BIBREF15.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
... as mentioned in the pre-training phase of transfer protocol, we ﬁrst pre-train MLM on monolingual data of both source and pivot lan- guages, then leverage the parameters of MLM to initialize TLM and the proposed BRLM, which are continued to be optimized with source-pivot bilingual data. In our experi- ments, we use MLM+TLM, MLM+BRLM to represent this training process. For the masking strategy during training, following Devlin et al. (2018), 15% of BPE tokens are se- lected to be masked. Among the selected tokens, 80% of them are replaced with [MASK] token, 10% are replaced 2 https://github.com/moses-smt/mosesdecoder/blob/RELEASE- 3.0/scripts/tokenizer/tokenizer.perl 3 https://github.com/facebookresearch/XLM with a random BPE token, and 10% unchanged. The predic- tion accuracy of masked words is used as a stopping cri- terion in the pre-training stage. Besides, we use fastalign tool (Dyer, Chahuneau, and Smith 2013) to extract word alignments for BRLM-HA. Main Results Table 2 and 3 report zero-shot results on Europarl and Multi-UN evaluation sets, respectively. We compare our ap- proaches with related approaches of pivoting, multilingual NMT (MNMT) (Johnson et al. 2016), and cross-lingual transfer without pretraining (Kim, Gao, and Ney 2019). The results show that our approaches consistently outperform other approaches across languages and datasets, especially surpass pivoting, which is a strong baseline in the zero-
shot scenario that multilingual NMT systems often fail to
beat (Johnson et al. 2016; Al-Shedivat and Parikh 2019;
Arivazhagan et al. 2018). Pivoting translates source to
pivot then to target in two steps, causing inefﬁcient trans-
lation process. Our approaches use one encoder-decoder
model to translate between any zero-shot directions, which
is more efﬁcient than pivoting. Regarding the comparison
between transfer approaches, our cross-lingual pretraining
based transfer outperforms transfer method that does not use
pretraining by a large margin.
Results on Europarl Dataset.
Regarding comparison be-
tween the baselines in table 2, we ﬁnd that pivoting is the
strongest baseline that has signiﬁcant advantage over other
two baselines. Cross-lingual transfer for languages without
shared vocabularies (Kim, Gao, and Ney 2019) manifests the
worst performance because of not using source ↔ pivot par-
allel data, which is utilized as beneﬁcial supervised signal for the other two baselines. Our best approach of MLM+BRLM-SA achieves the sig- niﬁcant superior performance to all baselines in the zero- shot directions, improving by 0.9-4.8 BLEU points over the strong pivoting. Meanwhile, in the supervised direction of pivot → target, our approaches performs even better than the original supervised Transformer thanks to the shared en- MultiUN Ar,Es,Ru ↔ En Direction Ar → Es Es → Ar Ar → Ru Ru → Ar Es → Ru Ru → Es A-ZST A-ST Baselines Cross-lingual Transfer 10.26 12.44 4.58 4.42 13.80 7.93 8.90 44.73 MNMT(Johnson et al. 2016) 27.40 20.18 15.12 16.19 17.88 27.93 20.78 43.95 Pivoting m 42.29 30.15 27.23 26.16 29.57 40.08 32.58 43.95 Proposed Cross-lingual Pretraining Based Transfer MLM 16.50 23.41 9.61 14.23 22.80 23.66 18.36 44.25 MLM+TLM 25.98 26.55 16.84 20.07 25.91 29.52 24.14 43.71 MLM+BRLM-HA 29.05 27.58 18.10 20.42 25.39 30.96 25.25 44.67 MLM+BRLM-SA 36.01 31.08 25.49 25.06 30.47 36.01 30.68 44.54 Adding Back Translation MNMT* (Gu et al. 2019) 39.72 28.05 24.67 24.43 27.41 38.01 30.38 43.98 MLM 40.98 31.53 26.06 26.69 31.28 40.02 32.76 44.28 MLM+TLM 41.15 29.77 27.61 27.74 31.02 40.37 32.39 44.14 MLM+BRLM-HA 41.74 31.89 27.24 27.54 31.29 40.34 33.35 44.52 ...

---

In this paper, we propose a cross-lingual pretraining based
transfer approach for the challenging zero-shot translation
task, in which source and target languages have no parallel
data, while they both have parallel data with a high resource
(a) MLM
(b) MLM+TLM
(c) MLM+BRLM-HA
(d) MLM+BRLM-SA
Figure 4: Cosine similarity visualization at word level given
an English-Russian sentence pair from the MultiUN valida-
tion sets. Brighter indicates higher similarity.
Freezing Layers
En → Ru
Ar → Ru
Es → Ru
None
37.80
16.09
19.80
2
37.79
21.47
28.35
4
37.55
25.49
30.47
6
35.31
22.90
28.22
Table 4: BLEU score of freezing different layers. The num-
ber in Freezing Layers column denotes that the number of
encoder layers will not be updated.
pivot language. With the aim of building the language in-
variant representation between source and pivot languages
for smooth transfer of the parent model of pivot → target di-
rection to the child model of source → target direction, we in-
troduce one monolingual pretraining method and two bilin-
gual pretraining methods to construct an universal encoder
for the source and pivot languages. Experiments on public
datasets show that our approaches signiﬁcantly outperforms
several strong baseline systems, and manifest the language
invariance characteristics in both sentence level and word
level neural representations.
Acknowledgments
We would like to thank the anonymous reviewers for the
helpful comments. This work was supported by National
Key R&D Program of China (Grant No. 2016YFE0132100),
National Natural Science Foundation of China (Grant No.
61525205, 61673289). This work was also partially sup-
ported by Alibaba Group through Alibaba Innovative Re-
search Program and the Priority Academic Program Devel-
opment (PAPD) of Jiangsu Higher Education Institutions.

---

In recent years, zero-shot translation in NMT has attracted
widespread attention in academic research. Existing meth-
ods are mainly divided into four categories: pivot-based
method, transfer learning, multilingual NMT, and unsuper-
vised NMT.
• Pivot-based Method is a common strategy to obtain a
source → target model by introducing a pivot language.
This approach is further divided into pivoting and pivot-
synthetic. While the former ﬁrstly translates a source lan-
guage into the pivot language which is later translated
to the target language (Kauers et al. 2002; de Gispert
and Mariño 2006; Utiyama and Isahara 2007), the lat-
ter trains a source → target model with pseudo data gener-
ated from source-pivot or pivot-target parallel data (Chen
et al. 2017; Zheng, Cheng, and Liu 2017). Although the
pivot-based methods can achieve not bad performance, it
always falls into a computation-expensive and parameter-
vast dilemma of quadratic growth in the number of source languages, and suffers from the error propagation prob- lem (Zhu et al. 2013). • Transfer Learning is ﬁrstly introduced for NMT by Zoph et al. (2016), which leverages a high-resource par- ent model to initialize the low-resource child model. On this basis, Nguyen and Chiang (2017) and Kocmi and Bojar (2018) use shared vocabularies for source/target language to improve transfer learning, while Kim, Gao, and Ney (2019) relieve the vocabulary mismatch by mainly using cross-lingual word embedding. Although these methods are successful in the low-resource scene, they have limited effects in zero-shot translation. • Multilingual NMT (MNMT) enables training a single model that supports translation from multiple source lan- guages into multiple target languages, even those unseen language pairs (Firat, Cho, and Bengio 2016; Firat et al. 2016; Johnson et al. 2016; Al-Shedivat and Parikh 2019; Aharoni, Johnson, and Firat 2019). Aside from sim- pler deployment, MNMT beneﬁts from transfer learning where low-resource language pairs are trained together with high-resource ones. However, Gu et al. (2019) point out that MNMT for zero-shot translation easily fails, and is sensitive to the hyper-parameter setting. Also, MNMT usually performs worse than the pivot-based method in zero-shot translation setting (Arivazhagan et al. ...
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Context defines pivoting vs pivot-synthetic and shows Pivoting_m in the MultiUN table.

## CEC-03

**Question:** Do they evaluate only on English datasets?

**Reference answer(s):** Yes

<details><summary>Gold evidence</summary>

> Specifically, we conducted a feature ablation study to assess the informativeness of each feature group and a feature elimination study to determine the optimal feature sets for classifying Twitter tweets. We leveraged an existing, annotated Twitter dataset that was constructed based on a hierarchical model of depression-related symptoms BIBREF12 , BIBREF13 . The dataset contains 9,473 annotations for 9,300 tweets. Each tweet is annotated as no evidence of depression (e.g., “Citizens fear an economic depression") or evidence of depression (e.g., “depressed over disappointment"). If a tweet is annotated evidence of depression, then it is further annotated with one or more depressive symptoms, for example, depressed mood (e.g., “feeling down in the dumps"), disturbed sleep (e.g., “another restless night"), or fatigue or loss of energy (e.g., “the fatigue is unbearable") BIBREF10 . For each class, every annotation (9,473 tweets) is binarized as the positive class e.g., depressed mood=1 or negative class e.g., not depressed mood=0.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
In summary, we conducted two feature study experiments
to assess the contribution of feature groups and to determine
the optimal percentile of top ranked features for classifying
Twitter tweets in the depression schema hierarchy.
From
these experiments, we conclude that simple lexical features
and reduced feature sets can produce comparable results to
the much larger feature dataset.

---

Speciﬁcally, we conducted a feature ablation study to as-
sess the informativeness of each feature group and a feature
elimination study to determine the optimal feature sets for
classifying Twitter tweets. We leveraged an existing, anno-
tated Twitter dataset that was constructed based on a hier-
archical model of depression-related symptoms [13, 14]. The
dataset contains 9,473 annotations for 9,300 tweets. Each
tweet is annotated as no evidence of depression (e.g., “Cit-
izens fear an economic depression”) or evidence of depres-
sion (e.g., “depressed over disappointment”). If a tweet is
annotated evidence of depression , then it is further anno-
tated with one or more depressive symptoms , for example,
depressed mood (e.g.,“feeling down in the dumps”), disturbed
sleep (e.g., “another restless night”), or fatigue or loss of en-
ergy (e.g., “the fatigue is unbearable”) [12]. For each class,
every annotation (9,473 tweets) is binarized as the positive
class e.g., depressed mood=1 or negative class e.g., not de-
pressed mood=0 .

---

Unsurprisingly, lexical features (unigrams) were the largest
contributor to feature counts in the dataset. We observed
that lexical features are also critical for identifying depres-
sive symptoms , speciﬁcally for depressed mood and for dis-
turbed sleep .
For the classes higher in the hierarchy - no
evidence of depression , evidence of depression , and depres-
sive symptoms - the classiﬁer produced consistent F1-scores,
even slightly above the baseline for depressive symptoms and
minor ﬂuctuations of change in recall and precision when
removing other feature groups suggesting that the contri-
bution of non- lexical features to classiﬁcation performance
was limited. However, notable changes in F1-score were ob-
served for the classes lower in the hierarchy including dis-
turbed sleep and fatigue or loss of energy .
For instance,
changes in F1-scores driven by both recall and precision
were observed for disturbed sleep by ablating demograph-
0
10
20
30
40
50
60
70
80
90
100
1
5
10
15
20
25
30
35
40
45
50
55
60
65
70
75
80
85
90
95
F1-­‐score
Feature	
  Percen/le
No	
  evidence	
  of	
  depression
Evidence	
  of	
  depression
Depressive	
  symptoms
Disturbed	
  sleep
Depressed	
  mood
FaBgue	
  or	
  loss	
  of	
  energy
Figure 2: Feature elimination study: for each class, we plotted the change of average F1-scores for top features
of percentiles by adding top-ranked features at 5% increments to the prediction model.
ics , emotion , and sentiment features, suggesting that age
or gender (“mid-semester exams have me restless”), polar-
ity and subjective terms (“lack of sleep is killing me”), and
emoticons (“wide awake :(”) could be important for both
identifying and correctly classifying a subset of these tweets.

---

The utility of Twitter data as a medium to support population-
level mental health monitoring is not well understood. In
an eﬀort to better understand the predictive power of super-
vised machine learning classiﬁers and the inﬂuence of feature
sets for eﬃciently classifying depression-related tweets on a
large-scale, we conducted two feature study experiments. In
the ﬁrst experiment, we assessed the contribution of fea-
ture groups such as lexical information (e.g., unigrams) and
emotions (e.g., strongly negative) using a feature ablation
study. In the second experiment, we determined the per-
centile of top ranked features that produced the optimal
classiﬁcation performance by applying a three-step feature
elimination approach. In the ﬁrst experiment, we observed
that lexical features are critical for identifying depressive
symptoms , speciﬁcally for depressed mood (-35 points) and
for disturbed sleep (-43 points). In the second experiment,
we observed that the optimal F1-score performance of top
ranked features in percentiles variably ranged across classes
e.g., fatigue or loss of energy (5th percentile, 288 features)
to depressed mood (55th percentile, 3,168 features) suggest-
ing there is no consistent count of features for predicting
depressive-related tweets. We conclude that simple lexical
features and reduced feature sets can produce comparable
results to larger feature sets.
CCS Concepts
• Computing methodologies → Feature selection; Su-
pervised learning by classiﬁcation; Support vector machines;
Natural language processing;
Keywords
depression; natural language processing; social media

---

[12] D. Mowery, A. Park, C. Bryan, and M. Conway.
Towards automatically classifying depressive
symptoms from Twitter data for population health. In
Proceedings of the Workshop on Computational
Modeling of People’s Opinions, Personality, and
Emotions in Social Media , pages 182–191, Osaka,
Japan, December 2016.
[13] D. L. Mowery, C. Bryan, and M. Conway. Toward
developing an annotation scheme for depressive
disorder symptoms: A preliminary study using
Twitter data. In Proceeding of 2nd Workshop on
Computational Linguistics and Clinical Psychology -
From Linguistic Signal to Clinical Reality , pages
89–98. Association for Computational Linguistics,
2015.
[14] D. L. Mowery, H. A. Smith, T. Cheney, G. Stoddard,
C. Glen, C. Bryan, and M. Conway. Understanding
depressive symptoms and psychosocial stressors on
Twitter: A corpus-based study. J Med Internet Res ,
[ in press ].
[15] M. Mysl´ın, S.-H. Zhu, W. W. Chapman, and
M. Conway. Using Twitter to examine smoking
behavior and perceptions of emerging tobacco
products. J Med Internet Res , 15(8):e174, 2013.
[16] J. Pennebaker, M. Francis, and R. Booth. Linguistic
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Gold dataset paragraph (English Twitter depression tweets) is present verbatim.

## CEC-04

**Question:** What modern MRC gold standards are analyzed?

**Reference answer(s):** fit our problem definition and were published in the years 2016 to 2019, have at least $(2019 - publication\ year) \times 20$ citations ‖ MSMARCO,  HOTPOTQA, RECORD,  MULTIRC, NEWSQA, and DROP.

<details><summary>Gold evidence</summary>

> We select contemporary MRC benchmarks to represent all four commonly used problem definitions BIBREF15. In selecting relevant datasets, we do not consider those that are considered “solved”, i.e. where the state of the art performance surpasses human performance, as is the case with SQuAD BIBREF28, BIBREF7. Concretely, we selected gold standards that fit our problem definition and were published in the years 2016 to 2019, have at least $(2019 - publication\ year) \times 20$ citations, and bucket them according to the answer selection styles as described in Section SECREF4 We randomly draw one from each bucket and add two randomly drawn datasets from the candidate pool. This leaves us with the datasets described in Table TABREF19. For a more detailed description, we refer to Appendix .

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
qualitative error analy- ses for a proposed approach. Furthermore we applied the framework to analyse popular state-of-the-art gold standards for machine reading com- prehension: We reveal issues with their factual correct- ness, show the presence of lexical cues and we observe that semantics-altering grammatical modiﬁers are missing in all of the investigated gold standards. Studying how to introduce those modiﬁers into gold standards and observing whether state-of-the-art MRC models are capable of per- forming reading comprehension on text containing them, is a future research goal. A future line of research is to extend the framework to be able to identify the different types of exploitable cues such as question or entity typing and concrete overlap pat- terns. This will allow the framework to serve as an inter- pretable estimate of reading comprehension complexity of gold standards. Finally, investigating gold standards un- der this framework where MRC models outperform the hu- man baseline (e.g. SQ U AD) will contribute to a deeper un- derstanding of the seemingly superb performance of deep learning approaches on them. Abadi, M., Barham, P., Chen, J., Chen, Z., Davis, A., Dean, J., Devin, M., Ghemawa, S., Irving, G., Isard, M., Kud- lur, M., Levenberg, J., Monga, R., Moore, S., Murray, D. G., Steiner, B., Tucker, P., Vasudevan, V., Warden, P., Wicke, M., Yu, Y., and Zheng, X. (2016). Tensor- ﬂow: A system for large-scale machine learning. In 12th USENIX Symposium on Operating Systems Design and Implementation (OSDI 16) , pages 265–283. Berant, J., Chou, A., Frostig, R., and Liang, P. (2013). Semantic Parsing on Freebase from Question-Answer Pairs. In Proceedings of the 2013 Conference on Em- pirical Methods in Natural Language Processing , pages 1533–1544. Boratko, M., Padigela, H., Mikkilineni, D., Yuvraj, P., Das, R., McCallum, A., Chang, M., Fokoue-Nkoutche, A., Kapanipathi, P., Mattei, N., Musa,

---

it evaluates. More importantly, it allows to draw comparisons between multiple gold stan- dards and between the results of respective state-of-the-art models that are evaluated on them. In this work, we take a step back and propose a frame- work to systematically analyse MRC evaluation data, typi- cally a set of questions and expected answers to be derived from accompanying passages. Concretely, we introduce a methodology to categorise the linguistic complexity of the textual data and the reasoning and potential external knowl- edge required to obtain the expected answer. Additionally we propose to take a closer look at the factual correctness of the expected answers, a quality dimension that appears under-explored in literature. We demonstrate the usefulness of the proposed framework by applying it to precisely describe and compare six con- temporary MRC datasets. Our ﬁndings reveal concerns about their factual correctness, the presence of lexical cues that simplify the task of reading comprehension and the lack of semantic altering grammatical modiﬁers. We re- lease the raw data comprised of 300 paragraphs, questions and answers richly annotated under the proposed frame- work as a resource for researchers developing natural lan- guage understanding models and datasets to utilise further. To the best of our knowledge this is the ﬁrst attempt to in- troduce a common evaluation methodology for MRC gold standards and the ﬁrst across-the-board qualitative evalu- ation of MRC datasets with respect to the proposed cate- gories. Analysis 2.1. Problem deﬁnition We deﬁne the task of machine reading comprehension, the target application of the proposed methodology as follows: Given a paragraph P that consists of tokens (words) p 1 , . . . , p n P and a question Q that consists of to- kens q 1 . . . q n Q , the goal is to retrieve

---

arXiv:2003.04642v1 [cs.CL] 10 Mar 2020 A Framework for Evaluation of Machine Reading Comprehension Gold Standards Viktor Schlegel, Marco Valentino, Andr´e Freitas, Goran Nenadic, Riza Batista-Navarro Department of Computer Science, University of Manchester Manchester, United Kingdom { viktor.schlegel, marco.valentino, andre.freitas, gnenadic, riza.batista } @manchester.ac.uk Machine Reading Comprehension (MRC) is the task of answering a question over a paragraph of text. While neural MRC systems gain popularity and achieve noticeable performance, issues are being raised with the methodology used to establish their performance, particularly concerning the data design of gold standards that are used to evaluate them. There is but a limited understanding of the challenges present in this data, which makes it hard to draw comparisons and formulate reliable hypotheses. As a ﬁrst step towards alleviating the problem, this paper proposes a unifying framework to systematically investigate the present linguistic features, required reasoning and background knowledge and factual correctness on one hand, and the presence of lexical cues as a lower bound for the requirement of understanding on the other hand. We propose a qualitative annotation schema for the ﬁrst and a set of approximative metrics for the latter. In a ﬁrst application of the framework, we analyse modern MRC gold standards and present our ﬁndings: the absence of features that contribute towards lexical ambiguity, the varying factual correctness of the expected answers and the presence of lexical cues, all of which potentially lower the reading comprehension complexity and quality of the evaluation data. Keywords: Machine Reading Comprehension, Question Answering, Evaluation Methodology, Annotation Schema There is a recent spark of interest in the task of Question Answering (QA) over unstructured textual data, also re- ferred to as Machine Reading Comprehension (MRC). This is mostly due to wide-spread success of advances in various facets of deep learning related research, such as novel

---

A is an unconstrained natural lan- guage string. A gold standard G is composed of m entries ( Q i , A i , P i ) i ∈{ 1 ,...,m } . The performance of an approach is established by compar- ing its answer predictions A ∗ i on the given input ( Q i , T i ) (and A i for the multiple choice setting) against the expected answer A i for all i ∈{ 1 , . . . , m } under a performance metric. Typical performance metrics are exact match (EM) or accuracy , i.e. the percentage of exactly predicted an- swers, and the F1 score – the harmonic mean between the precision and the recall of the predicted tokens compared to expected answer tokens. The overall F1 score can ei- ther be computed by averaging the F1 scores for every in- stance or by ﬁrst averaging the precision and recall and then computing the F1 score from those averages (macro F1). Free-text answers, meanwhile, are evaluated by means of text generation and summarisation metrics such as BLEU (Papineni et al., 2001) or ROUGE-L (Lin, 2004). In this section we describe a methodology to categorise gold standards according to linguistic complexity, required reasoning and background knowledge, and their factual correctness. Speciﬁcally, we use those dimensions as high- level categories of a qualitative annotation schema for an- notating question, expected answer and the corresponding context. We further enrich the qualitative annotations by a metric based on lexical cues in order to approximate a lower bound for the complexity of the reading comprehen- Annotation Schema Supporting Fact Answer Type Paraphrasing - Generated Span - Unanswerable Correctness Debatable - Wrong Reasoning Operational Bridge - Comparison - Constraint - Intersection Arithmetic Substraction - Addition Ordering - Counting -
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Says 'six contemporary MRC datasets' but never names them or gives selection criteria.

## CEC-05

**Question:** Do they evaluate only on English datasets?

**Reference answer(s):** Yes

<details><summary>Gold evidence</summary>

> For both POS tagging and dependency parsing, we run experiments on the Wall Street Journal (WSJ) portion of the Penn Treebank. To create the observed data embeddings, we train skip-gram word embeddings BIBREF7 that are found to capture syntactic properties well when trained with small context window BIBREF8 , BIBREF9 . Following BIBREF9 , the dimensionality INLINEFORM0 is set to 100, and the training context window size is set to 1 to encode more syntactic information. The skip-gram embeddings are trained on the one billion word language modeling benchmark dataset BIBREF21 in addition to the WSJ corpus.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
In this section, we ﬁrst describe our datasets and
experimental setup. We then instantiate our ap-
proach with Markov and DMV-structured syntax
models, and report results on POS tagging and de-
pendency grammar induction respectively. Lastly,
we analyze the learned latent embeddings.

---

based word embeddings. In Proceedings of ACL .
Chu-Cheng Lin, Waleed Ammar, Chris Dyer, and Lori
Levin. 2015. Unsupervised pos induction with word
embeddings. In Proceedings of the NAACL-HLT .
Laurens van der Maaten and Geoffrey Hinton. 2008.
Visualizing data using t-sne.
Journal of Machine
Learning Research .
Mitchell P Marcus, Mary Ann Marcinkiewicz, and
Beatrice Santorini. 1993. Building a large annotated
corpus of english: The penn treebank.
Computa-
tional linguistics , 19(2):313–330.
Yishu Miao and Phil Blunsom. 2016. Language as a
latent variable: Discrete generative models for sen-
tence compression. In Proceedings of EMNLP .
Tomas Mikolov, Kai Chen, Greg Corrado, and Jef-
frey Dean. 2013.
Efﬁcient estimation of word
representations in vector space.
arXiv preprint
arXiv:1301.3781 .
John K Pate and Sharon Goldwater. 2013.
Unsu-
pervised dependency parsing with acoustic cues.
Transactions of the Association for Computational
Linguistics .
John K Pate and Mark Johnson. 2016. Grammar in-
duction from (lots of) words alone. In Proceedings
of COLING .
Matthew E Peters, Mark Neumann, Mohit Iyyer, Matt
Gardner, Christopher Clark, Kenton Lee, and Luke
Zettlemoyer. 2018. Deep contextualized word rep-
resentations. In Proceedings of HLT-NAACL .
Danilo Jimenez Rezende and Shakir Mohamed. 2015.
Variational inference with normalizing ﬂows.
In
Proceedings of ICML .
Andrew Rosenberg and Julia Hirschberg. 2007.
V-
measure: A conditional entropy-based external clus-
ter evaluation measure. In Proceedings of EMNLP-
CoNLL .
Valentin I Spitkovsky, Hiyan Alshawi, Angel X Chang,

---

72.0 ∗
64.4 ∗
Neural E-DMV ( Jiang et al. , 2016 )
55.3
42.7
CRFAE ( Cai et al. , 2017 )
37.2
29.5
Gaussian DMV
55.4 (1.3)
43.1 (1.2)
Ours (4 layers)
58.4 (1.9)
46.2 (2.3)
Ours (8 layers)
60.2 (1.3)
47.9 (1.2)
Ours (16 layers)
54.1 (8.5)
43.9 (5.7)
w/ gold POS tags (for reference only)
DMV ( Klein and Manning , 2004 )
55.1
39.7
UR-A E-DMV ( Tu and Honavar , 2012 )
71.4
57.0
MaxEnc ( Le and Zuidema , 2015 )
73.2
65.8
Neural E-DMV ( Jiang et al. , 2016 )
72.5
57.6
CRFAE ( Cai et al. , 2017 )
71.7
55.7
L-NDMV (Big training data) ( Han et al. , 2017 )
77.2
63.2
Table 2 : Directed dependency accuracy on section 23 of
WSJ, evaluating on sentences of length ⩽ 10 and all lengths.
Starred entries ( ∗ ) denote that the system beneﬁts from ad-
ditional punctuation-based constraints. Standard deviation is
given in parentheses when available.
parameters are initialized in the same way as in
the POS tagging experiment. The directed depen-
dency accuracy (DDA) is used for evaluation and
we report accuracy on sentences of length ⩽ 10
and all lengths. We train the parser until training
data likelihood converges, and report the mean and
standard deviation over 20 random restarts.
Comparison with other related work.
Our
model directly observes word embeddings and
does not require gold POS tags during training.
Thus, results from related work trained on gold
tags are not directly comparable.
However, to
measure how these systems might perform with-
out gold tags, we run three recent state-of-the-
art systems in our experimental setting:
UR-
A E-DMV ( Tu and Honavar , 2012 ), Neural E-

---

or annotated data from related languages ( Cohen
et al. , 2011 ). Our approach is naturally designed
to train on word embeddings directly, thus we at-
tempt to induce dependencies without using gold
POS tags or other extra linguistic information.
Setup.
Like previous work we use sections 02-
21 of WSJ corpus as training data and evaluate
on section 23, we remove punctuations and train
the models on sentences of length ⩽ 10 , “head-
percolation” rules ( Collins , 1999 ) are applied to
obtain gold dependencies for evaluation. We train
basic DMV, extended DMV (E-DMV) ( Head-
den III et al. , 2009 ) and Gaussian DMV (which
treats POS tag as unknown latent variables and
generates observed word embeddings directly
conditioned on them following Gaussian distri-
bution) as baselines.
Basic DMV and E-DMV
are trained with Viterbi EM ( Spitkovsky et al. ,
2010 ) on unsupervised POS tags induced from
our Markov-structured model described in § 4.3 .
Multinomial parameters of the syntax model in
both Gaussian DMV and our model are initial-
ized with the pre-trained DMV baseline. Other
System
⩽ 10
all
w/o gold POS tags
DMV ( Klein and Manning , 2004 )
49.6
35.8
E-DMV ( Headden III et al. , 2009 )
52.1
38.2
UR-A E-DMV ( Tu and Honavar , 2012 )
58.9
46.1
CS ∗ ( Spitkovsky et al. , 2013 )
72.0 ∗
64.4 ∗
Neural E-DMV ( Jiang et al. , 2016 )
55.3
42.7
CRFAE ( Cai et al. , 2017 )
37.2
29.5
Gaussian DMV
55.4 (1.3)
43.1 (1.2)
Ours (4 layers)
58.4 (1.9)
46.2 (2.3)
Ours (8 layers)
60.2 (1.3)
47.9 (1.2)
Ours (16 layers)
54.1 (8.5)
43.9 (5.7)
w/ gold POS tags (for reference only)

---

Variational inference with normalizing ﬂows.
In
Proceedings of ICML .
Andrew Rosenberg and Julia Hirschberg. 2007.
V-
measure: A conditional entropy-based external clus-
ter evaluation measure. In Proceedings of EMNLP-
CoNLL .
Valentin I Spitkovsky, Hiyan Alshawi, Angel X Chang,
and Daniel Jurafsky. 2011a. Unsupervised depen-
dency parsing without gold part-of-speech tags. In
Proceedings of EMNLP .
Valentin I Spitkovsky, Hiyan Alshawi, and Daniel Ju-
rafsky. 2011b. Punctuation: Making a point in un-
supervised dependency parsing. In Proceedings of
CoNLL .
Valentin I Spitkovsky, Hiyan Alshawi, and Daniel
Jurafsky. 2012.
Capitalization cues improve de-
pendency grammar induction.
In Proceedings of
NAACL-HLT Workshop on the Induction of Linguis-
tic Structure .
Valentin I Spitkovsky, Hiyan Alshawi, and Daniel Ju-
rafsky. 2013.
Breaking out of local optima with
count transforms and model recombination: A study
in grammar induction. In Proceedings of EMNLP .
Valentin I Spitkovsky, Hiyan Alshawi, Daniel Jurafsky,
and Christopher D Manning. 2010. Viterbi training
improves unsupervised dependency parsing. In Pro-
ceedings of CoNLL .
Karl Stratos, Michael Collins, and Daniel Hsu. 2016.
Unsupervised part-of-speech tagging with anchor
hidden markov models. Transactions of the Asso-
ciation for Computational Linguistics .
Ke M Tran, Yonatan Bisk, Ashish Vaswani, Daniel
Marcu, and Kevin Knight. 2016. Unsupervised neu-
ral hidden markov models. In Proceedings of the
Workshop on Structured Prediction for NLP .
Kewei Tu and Vasant Honavar. 2012.
Unambiguity
```
</details>

- **Judgment:** `[ ] YES   [X] NO   [ ] UNSURE`
- **Note (optional):** DEFERRED (Claude unsure): WSJ section 23 used for parsing and Penn Treebank cited as English, but POS-tagging dataset not stated in this context. Leaning YES.
(human) they can answer yes on one dataset only so no

## CEC-06

**Question:** what was the baseline?

**Reference answer(s):** system presented by deri2016grapheme ‖ wFST

<details><summary>Gold evidence</summary>

> Results on LangID and NoLangID are compared to the system presented by deri2016grapheme, which is identified in our results as wFST. Their results can be divided into two parts:

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
We present experiments with two versions of our
sequence-to-sequence model.
LangID prepends
each training, validation, and test sample with
an artiﬁcial token identifying the language of the
sample. NoLangID omits this token. LangID and
NoLangID have identical structure otherwise. To
translate the test corpus, we used a beam width of
100. Although this is an unusually wide beam and
had negligible performance effects, it was neces-
sary to compute our error metrics.

---

On the 229 languages for which Deri and Knight
( 2016 ) presented their ﬁnal results, the LangID
version of our system outperforms the baseline by
a wide margin. The best performance came with
the version of our model that was trained on data
in all available languages, not just the languages
it was tested on. Using a language ID token im-
proves results considerably, but even NoLangID
beats the baseline in WER and WER 100. Full
results are presented in Table 4 .
Model
WER
WER 100
PER
wFST
88.04
69.80
48.01
LangID-High
74.99
46.18
42.64
LangID-Adapted
75.06
46.39
41.77
LangID-All
74.10
43.23
37.85
NoLangID-High
82.14
50.17
54.05
NoLangID-Adapted
85.11
48.24
55.93
NoLangID-All
83.65
47.13
51.87
Table 4: Adapted Results

---

Our approach is similar in goal to Deri and Knight
( 2016 )’s model for adapting high resource g2p
models for low resource languages. They trained
weighted ﬁnite state transducer (wFST) models on
a variety of high resource languages, then trans-
ferred those models to low resource languages, us-
ing a language distance metric to choose which
high resource models to use and a phoneme dis-
tance metric to map the high resource language’s
phonemes to the low resource language’s phoneme
inventory. These distance metrics are computed
based on data from Phoible ( Moran et al. , 2014 )
and URIEL ( Littell et al. , 2017 ).
Other low resource g2p systems have used a
strategy of combining multiple models. Schlippe
et al. ( 2014 ) trained several data-driven g2p sys-
tems on varying quantities of monolingual data
and combined their outputs with a phoneme-level
voting scheme. This led to improvements over the
best-performing single system for small quantities
of data in some languages. Jyothi and Hasegawa-
Johnson ( 2017 ) trained recurrent neural networks
for small data sets and found that a version of their
system that combined the neural network output
arXiv:1708.01464v1  [cs.CL]  4 Aug 2017
with the output of the wFST-based Phonetisaurus
system ( Novak et al. , 2016 ) did better than either
system alone.
A different approach came from Kim and Sny-
der ( 2012 ), who used supervised learning with
an undirected graphical model to induce the
grapheme–phoneme mappings for languages writ-
ten in the Latin alphabet. Given a short text in
a language, the model predicts the language’s or-

---

Having shown that our model exceeds the perfor-
mance of the wFST-adaptation approach, we next
compare it to the baseline models for just high
resource languages. The wFST models here are
purely monolingual – they do not use data adap-
tation because there is sufﬁcient training data for
each of them. Full results are presented in Table 5 .
We omit models trained on the Adapted languages
because they were not trained on high resource
languages with unique writing systems, such as
Georgian and Greek, and consequently performed
very poorly on them.
In contrast to the larger-scale Adapted results,
in the High Resource experiments none of the
sequence-to-sequence approaches equal the per-
formance of the wFST model in WER and PER,
although LangID-High does come close.
The
LangID models do beat wFST in WER 100. A
possible explanation is that a monolingual wFST
model will never generate phonemes that are not
part of the language’s inventory. A multilingual
model, on the other hand, could potentially gener-
ate phonemes from the inventories of any language
it has been trained on.
Even if LangID-High does not present a more
accurate result, it does present a more compact
one: LangID-High is 15.4 MB, while the com-
bined wFST high resource models are 197.5 MB.
Model
WER
WER 100
PER
wFST
44.17
21.97
14.70
LangID-High
47.88
15.50
16.89
LangID-All
48.76
15.78
17.35
NoLangID-High
69.72
29.24
35.16
NoLangID-All
69.82
29.27
35.47
Table 5: High Resource Results

---

lutionary Anthropology, Leipzig. http://wals.info/ .
Ben Hixon, Eric Schneider, and Susan L Epstein. 2011.
Phonemic similarity metrics to compare pronunci-
ation methods.
In Twelfth Annual Conference of
the International Speech Communication Associa-
tion (INTERSPEECH) . Florence, Italy, pages 825–
828.
Sepp Hochreiter and J¨urgen Schmidhuber. 1997.
Long short-term memory.
Neural computation
9(8):1735–1780.
Melvin Johnson, Mike Schuster, Quoc V Le, Maxim
Krikun, Yonghui Wu, Zhifeng Chen, Nikhil Thorat,
Fernanda Vi´egas, Martin Wattenberg, Greg Corrado,
et al. 2016. Google’s multilingual neural machine
translation system: Enabling zero-shot translation.
arXiv preprint arXiv:1611.04558 .
Preethi Jyothi and Mark Hasegawa-Johnson. 2017.
Low-resource grapheme-to-phoneme conversion us-
ing recurrent neural networks. In Proc. ICASSP .
Young-Bum Kim and Benjamin Snyder. 2012.
Uni-
versal grapheme-to-phoneme prediction over Latin
alphabets. In Proceedings of the 2012 Joint Con-
ference on Empirical Methods in Natural Language
Processing and Computational Natural Language
Learning . Association for Computational Linguis-
tics, pages 332–343.
G. Klein, Y. Kim, Y. Deng, J. Senellart, and A. M.
Rush. 2017.
OpenNMT: Open-Source Toolkit
for Neural Machine Translation.
arXiv preprint
arXiv:1701.02810 .
Kevin Lenzo. 2007. The CMU pronouncing dictionary.
Patrick Littell, David Mortensen, Ke Lin, Katherine
Kairis, Carlisle Turner, and Lori Levin. 2017. Uriel
and lang2vec: Representing languages as typolog-
ical, geographical, and phylogenetic vectors.
In
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Baseline = Deri & Knight (2016) wFST, explicitly in context and tables.

## CEC-07

**Question:** What dataset is used to train the model?

**Reference answer(s):** 2,50,000 tweets | Stock opening and closing prices of Microsoft from August 31st, 2015 to August 25th, 2016 ‖ Collected tweets and opening and closing stock prices of Microsoft.

<details><summary>Gold evidence</summary>

> A total of 2,50,000 tweets over a period of August 31st, 2015 to August 25th,2016 on Microsoft are extracted from twitter API BIBREF15 . Twitter4J is a java application which helps us to extract tweets from twitter. The tweets were collected using Twitter API and filtered using keywords like $ MSFT, # Microsoft, #Windows etc. Not only the opinion of public about the company's stock but also the opinions about products and services offered by the company would have a significant impact and are worth studying. Based on this principle, the keywords used for filtering are devised with extensive care and tweets are extracted in such a way that they represent the exact emotions of public about Microsoft over a period of time. The news on twitter about Microsoft and tweets regarding the product releases were also included. Stock opening and closing prices of Microsoft from August 31st, 2015 to August 25th, 2016 are obtained from Yahoo! Finance BIBREF16 .

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
The stock price data of Microsoft are labeled suitably for
training using a simple program. If the previous day stock
price is more than the current day stock price, the current
day is marked with a numeric value of 0, else marked with
a numeric value of 1. Now, this correlation analysis turns out
to be a classiﬁcation problem. The total positive, negative and
neutral emotions in tweets in a 3 day period are calculated
successively which are used as features for the classiﬁer model
and the output is the labeled next day value of stock 0 or 1.The
window size is experimented and best results are achieved
when the sentiment values precede 3 days to the stock price.
A total of 355 instances, each with 3 attributes are fed to the
classiﬁer with a split proportions of 80% train dataset and the
remaining dataset for testing. The accuracy of the classiﬁer is
discussed in the results section.

---

This section gives an overview of accuracy rates of the
trained classiﬁers. All the calculations are done in Weka tool
which runs on java virtual machine [20]
A. Sentiment Analyzer Results
The above sections discussed the method followed to train
the classiﬁer used for sentiment analysis of tweets. The
classiﬁer with features as Word2vec representations of human
annotated tweets trained on Random Forest algorithm with a
split percentage of 90 for training the model and remaining for
testing the model showed an accuracy of 70.2%. With N-gram
representations, the classiﬁer model with same algorithm and
with same dataset showed an accuracy of 70.5%. Though the
results are very close, model trained with word2vec represen-
tations is picked to classify the nonhuman annotated tweets
because of its promising accuracy for large datasets and the
sustainability in word meaning. Numerous studies have been
conducted on people and they concluded that the rate of human
concordance, that is the degree of agreement among humans
on the sentiment of a text, is between 70% and 79% [21]. They
have also synthesized that sentiment analyzers above 70% are
very accurate in most of the cases. Provided this information,
the results we obtained from the sentiment classiﬁcation can be
observed as very good ﬁgures while predicting the sentiments
in short texts, tweets, less than 140 characters in length.
Table-2 depicts the results of sentiment classiﬁcation including
accuracy, precision, F-measure and recall when trained with
different machine learning algorithms. ROC curves are plotted

---

far better, advanced and a recent technique which functions by
mapping words to a 300 dimensional vector representations.
Once every word of the language has been mapped to a
unique vector, vectors of words can be summed up yielding
a resultant vector for any given collection of words [19].
Relationship between the words is exactly retained in this form
of representation. Word vectors difference between Rome and
Italy is very close to the difference between vectors of France
and Paris This sustained relationship between word concepts
makes word2vec model very attractive for textual analysis.
In this representation, resultant vector which is sum of 300
dimensional vectors of all words in a tweet acts as features to
the model.
B. Model Training
The features extracted using the above methods for the
human annotated tweets are fed to the classiﬁer and trained
using random forest algorithm. Both the textual representations
performed well and the results are comparable. Out of the two,
model trained with word2vec representation is picked because
of its sustainability of meaning and promising performance
over large datasets. The results of sentiment classiﬁcation are
discussed in the following sections. The devised classiﬁer is
used to predict the emotions of non-human annotated tweets.
Table-1 shows a sample of annotated tweets by the sentiment
analyzer.

---

observed as very good ﬁgures while predicting the sentiments
in short texts, tweets, less than 140 characters in length.
Table-2 depicts the results of sentiment classiﬁcation including
accuracy, precision, F-measure and recall when trained with
different machine learning algorithms. ROC curves are plotted
for detailed analysis.
B. Stock Price and Sentiment Correlation Results
A classiﬁer is presented in the previous sections that is
trained with aggregate sentiment values for 3-day period as
features and the increase/decrease in stock price represented
by 1/0 as the output. Total data is split into two parts, 80
percent to train the model and remaining for testing operations.
The classiﬁer results show an accuracy value of 69.01% when
trained using Logistic regression algorithm and the accuracy
rate varied with the training set. When the model with LibSVM
is trained with 90 percent of data, it gave a result of 71.82%.
These results give a signiﬁcant edge to the investors and they
show good correlation between stock market movements and
the sentiments of public expressed in twitter. This trend shows
that with increasing dataset the models are performing well.
We would like to incorporate more data in our future work.

---

In this work, we have considered only twitter data for
analyzing people’s sentiment which may be biased because
not all the people who trade in stocks share their opinions on
twitter. Stocktwits [22] is a ﬁnancial communication platform
designed solely for sharing ideas and insights of investors,
entrepreneurs and traders. The current study can be extended
by incorporating stocktwits data. In addition to this, data from
news can also be included for an exhaustive public opinion
collection.
While training the sentiment analyzer, 3,216 tweets are used
which is comparatively a less number to train a sentiment
analyzer. In future, we look forward to human annotate more
than 10,000 tweets and train the classiﬁers. With increasing
size of training datasets, the models tend to perform better.
A CKNOWLEDGMENT
The authors would like to thank the students of IIT
Bhubaneswar who contributed to the human annotation of
tweets.
```
</details>

- **Judgment:** `[ ] YES   [X] NO   [ ] UNSURE`
- **Note (optional):** DEFERRED (Claude unsure): context says Microsoft stock price data + tweets (3,216 human-annotated), but not the 250k tweets or date range. Depends how strict you are vs the looser reference 'tweets + MSFT stock prices'. Leaning YES.

## CEC-08

**Question:** Why are prior knowledge distillation techniques models are ineffective in producing student models with vocabularies different from the original teacher models?  

**Reference answer(s):** While there has been existing work on reducing NLP model vocabulary sizes BIBREF15, distillation techniques cannot utilize these, since they require the student and teacher models to share the same vocabulary and output space. This profoundly limits their potential to further reduce model sizes. ‖ distillation techniques cannot utilize these, since they require the student and teacher models to share the same vocabulary and output space. This profoundly limits their potential to further reduce model sizes.

<details><summary>Gold evidence</summary>

> However, a significant bottleneck that has been overlooked by previous efforts is the input vocabulary size and its corresponding word embedding matrix, often accounting for a significant proportion of all model parameters. For instance, the embedding table of the BERTBASE model, comprising over 30K WordPiece tokens BIBREF14, accounts for over $21\%$ of the model size. While there has been existing work on reducing NLP model vocabulary sizes BIBREF15, distillation techniques cannot utilize these, since they require the student and teacher models to share the same vocabulary and output space. This profoundly limits their potential to further reduce model sizes.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Impact of vocabulary size: We trained a model
from scratch identical to BERT BASE except with
our 5K-WP student vocabulary. On the SST-2 and
MNLI-m dev sets, this model obtained 90.9% and
83.7% accuracy respectively - only 1.8% and 0.7%
lower respectively compared to BERT BASE .
Since embeddings account for a larger fraction
of model parameters with fewer layers, we trained
another model identical to our 6 × 256 model, but
with a 30K-WP vocabulary and teacher label dis-
tillation. This model showed small gains (0.1%
/ 0.5% accuracy on SST-2 / MNLI-m dev) over
our analogous distilled model, but with 30% more
parameters solely due to the larger vocabulary.
This suggests that a small WordPiece vocabulary
may be almost as effective for sequence classiﬁ-
cation/tagging tasks, especially for smaller BERT
models and up to moderately long inputs. Curi-
ously, increasing the student vocabulary size to 7K
or 10K did not lead to an increase in performance
on GLUE. We surmise that this may be due to un-
derﬁtting owing to the embeddings accounting for
a larger proportion of the model parameters.
Alternative vocabulary pruning: Probing other
strategies for a small-vocabulary model, we used
the above 6 × 256 30K-WP vanilla distilled model
to obtain a smaller model by pruning the vocab-
ulary to contain the intersection of the 30K and
5K vocabularies (total 4629 WPs). This model is
1.2% smaller than our 4928-WP distilled model,
but drops 0.8% / 0.7% on SST-2/MNLI-m dev sets.
Furthermore, to exploit the high overlap in vo-
cabularies, we tried running our distillation pipeline
but with the embeddings for student tokens (after
projecting up to the teacher dimension) also present
in the teacher vocabulary tied to the teacher em-
beddings for those tokens. This model, however,
dropped 0.7% / 0.5% on SST-2/MNLI-m compared
to our analogous 6 × 256 distilled model.
We also tried pretraining BERT LARGE from
scratch with the 5K vocabulary and doing vanilla
distillation for a 6 × 256 student:
this model
dropped 1.2% / 0.7% for SST-2/MNLI-m over our
similar distilled model, indicating the efﬁcacy of
mixed-vocabulary training over vanilla distillation.

---

Recently, pre-trained context-aware language mod-
els like ELMo ( Peters et al. , 2018 ), GPT ( Radford
et al. , 2019 ), BERT ( Devlin et al. , 2018 ) and XLNet
( Yang et al. , 2019 ) have outperformed traditional
word embedding models like Word2Vec ( Mikolov
et al. , 2013 ) and GloVe ( Pennington et al. , 2014 ),
and achieved strong results on a number of lan-
guage understanding tasks. However, these models
are typically too huge to host on mobile/edge de-
vices, especially for real-time inference. Recent
work has explored, inter alia, knowledge distilla-
tion ( Ba and Caruana , 2014 ; Hinton et al. , 2015 )
to train small-footprint student models by implicit
transfer of knowledge from a teacher model.
Most distillation methods, however, need the stu-
dent and teacher output spaces to be aligned. This
complicates task-agnostic distillation of BERT to
Asterisk ( * ) denotes equal contribution. Research con-
ducted when all authors were at Google.
smaller-vocabulary student BERT models since the
input vocabulary is also the output space for the
masked language modeling (MLM) task used in
BERT. This in turn limits these distillation meth-
ods’ ability to compress the input embedding ma-
trix, that makes up a major proportion of model
parameters e.g. the ∼ 30K input WordPiece embed-
dings of the BERT BASE model make up over 21%
of the model size. This proportion is even higher
for most distilled BERT models, owing to these
distilled models typically having fewer layers than
their teacher BERT counterparts.
We present a task and model-agnostic distillation
approach for training small, reduced-vocabulary
BERT models running into a few megabytes. In
our setup, the teacher and student models have
incompatible vocabularies and tokenizations for
the same sequence. We therefore align the stu-
dent and teacher WordPiece embeddings by train-
ing the teacher on the MLM task with a mix of
teacher-tokenized and student-tokenized words in
a sequence, and then using these student embed-
dings to train smaller student models. Using our
method, we train compact 6 and 12-layer reduced-
vocabulary student models which achieve competi-
tive performance in addition to high compression
for benchmark datasets as well as a real-world ap-
plication in language understanding for dialogue.

---

Pretrained language models like BERT have
achieved good results on NLP tasks, but are
impractical on resource-limited devices due to
memory footprint. A large fraction of this foot-
print comes from the input embeddings with
large input vocabulary and embedding dimen-
sions.
Existing knowledge distillation meth-
ods used for model compression cannot be di-
rectly applied to train student models with re-
duced vocabulary sizes. To this end, we pro-
pose a distillation method to align the teacher
and student embeddings via mixed-vocabulary
training. Our method compresses BERT LARGE
to a task-agnostic model with smaller vocab-
ulary and hidden dimensions, which is an or-
der of magnitude smaller than other distilled
BERT models and offers a better size-accuracy
trade-off on language understanding bench-
marks as well as a practical dialogue task.

---

WordPiece (WP) tokens ( Wu et al. , 2016 ) are sub-
word units obtained by applying greedy segmenta-
tion to a training corpus. Given such a corpus and
a number of desired tokens D , a WordPiece vocab-
ulary is generated by selecting D subword tokens
such that the resulting corpus is minimal in the num-
ber of WordPiece when segmented according to the
chosen WordPiece model. The greedy algorithm
for this optimization problem is described in more
detail in Sennrich et al. ( 2016 ). Most published
BERT models use a vocabulary of 30522 Word-
Pieces, obtained by running the above algorithm on
the Wikipedia and BooksCorpus ( Zhu et al. , 2015 )
corpora with a desired vocabulary size D of 30000.
For our student model, we chose a target vocab-
ulary size D of 5000 WordPiece tokens. Using the
same WordPiece vocabulary generation algorithm
and corpus as above, we obtain a 4928-WordPiece
vocabulary for the student model. This student vo-
cabulary includes all ASCII characters as separate
tokens, ensuring no out-of-vocabulary words upon
tokenization with this vocabulary. Additionally, the
30K teacher BERT vocabulary includes 93 . 9% of
the WP tokens in this 5K student vocabulary but
does not subsume it. We explore other strategies to
obtain a small student vocabulary in Section 6 .
For task-agnostic student models, we reuse
BERT’s masked language modeling (MLM) task:
words in context are randomly masked and pre-
dicted given the context via softmax over the
model’s WP vocabulary. Thus, the output spaces
for our teacher (30K) and student (5K) models are
unaligned. This, coupled with both vocabularies
tokenizing the same words differently, means exist-
ing distillation methods do not apply to our setting.
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Context states distillation needs aligned student/teacher output spaces, and vocab = MLM output space.

## CEC-09

**Question:** what were the baselines?

**Reference answer(s):** LF-MMI Attention
Seq2Seq 
RNN-T 
Char E2E LF-MMI 
Phone E2E LF-MMI 
CTC + Gram-CTC

<details><summary>Gold evidence</summary>

> We also evaluate the Jasper model's performance on a conversational English corpus. The Hub5 Year 2000 (Hub5'00) evaluation (LDC2002S09, LDC2005S13) is widely used in academia. It is divided into two subsets: Switchboard (SWB) and Callhome (CHM). The training data for both the acoustic and language models consisted of the 2000hr Fisher+Switchboard training data (LDC2004S13, LDC2005S13, LDC97S62). Jasper DR 10x5 was trained using SGD with momentum for 50 epochs. We compare to other models trained using the same data and report Hub5'00 results in Table TABREF31 .

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
... and R. Kompe, “Global opti- mization of a neural network-hidden markov model hybrid,” IEEE Transactions on Neural Networks, 3(2), 252259 , 1992. [3] A. Graves and J. Schmidhuber, “Framewise phoneme classiﬁca- tion with bidirectional lstm and other neural network architec- tures,” Neural Networks, vol. 18 , pp. 602–610, 2005. [4] G. Hinton et al. , “Deep neural networks for acoustic modeling in speech recognition,” IEEE Signal Processing Magazine , 2012. [5] A. Graves, S. Fern´andez, F. Gomez, and J. Schmidhuber, “Con- nectionist temporal classiﬁcation: labelling unsegmented se- quence data with recurrent neural networks,” in Proceedings of the 23rd international conference on Machine learning . ACM, 2006, pp. 369–376. [6] Y. Zhang et al. , “Towards end-to-end speech recognition with deep convolutional neural networks,” in Interspeech 2016 , 2016, pp. 410–414. [7] R. Collobert, C. Puhrsch, and G. Synnaeve, “Wav2letter: an end- to-end convnet-based speech recognition system,” arXiv preprint arXiv:1609.03193 , 2016. [8] V. Liptchinsky, G. Synnaeve, and R. Collobert, “Letter- based speech recognition with gated convnets,” arXiv preprint arXiv:1712.09444 , 2017. [9] Y. N. Dauphin, A. Fan, M. Auli, and D. Grangier, “Language modeling with gated convolutional networks,” in Proceedings of the 34th International Conference on Machine Learning - Volume 70 , ser. ICML’17.
JMLR.org, 2017, pp. 933–941.
[10] T. Salimans and D. P. Kingma, “Weight normalization:
A
simple reparameterization to accelerate training of deep neural
networks,”
in Advances in Neural Information Processing
Systems 29 , D. D. Lee, M. Sugiyama, U. V. Luxburg, I. Guyon,
and R. Garnett, Eds.
Curran Associates, Inc., 2016, pp.
901–909.
[11] S. Ioffe and C. Szegedy, “Batch normalization: Accelerating deep
network training by reducing internal covariate shift,” CoRR , vol.
abs/1502.03167, 2015.
[12] Z. Dai et al. ,
“Transformer-xl:
Language modeling with
longer-term dependency,” CoRR , vol. abs/1901.02860, 2018.
[13] V. Panayotov, G. Chen, D. Povey, and S. Khudanpur, “Lib-
rispeech: an asr corpus based on public domain audio books,” in
Acoustics, Speech and Signal Processing (ICASSP), 2015 IEEE
International Conference on .
IEEE, 2015, pp. 5206–5210.
[14] H. Hadian, H. Sameti, D. Povey, and S. Khudanpur, “End-to-end
speech recognition using lattice-free mmi,” in Proc. Interspeech 2018 , 2018, pp. 12–16. [15] D. P. Kingma and J. Ba, “Adam: A method for stochastic optimization,” CoRR , vol. abs/1412.6980, 2014. [16] G. Huang, Z. Liu, L. van der Maaten, and K. Q. Weinberger, “Densely connected convolutional networks,” arXiv preprint arXiv:1608.06993 , 2016. [17] J. Tang, Y. Song, L. Dai, and I. McLoughlin, “Acoustic modeling with densely connected residual network for multichannel speech recognition,” in Proc. Interspeech 2018 , 2018, pp. 1783–1787. [18] J. L. Ba, J. R. Kiros, and G. E. Hinton, “Layer normalization,” CoRR , vol. abs/1607.06450, 2016. [19] A. van den Oord et al. , “Conditional image generation with pixelcnn decoders,” in Advances in Neural Information Processing Systems 29 , D. D. Lee, M. Sugiyama, U. V. Luxburg, I. Guyon, and R. Garnett, Eds. Curran Associates, Inc., 2016, pp. 4790–4798. [20] C. Laurent, G. Pereyra, P. Brakel, Y. Zhang, and Y. Bengio, “Batch normalized recurrent neural networks,” in 2016 IEEE Interna- tional Conference on Acoustics, Speech and Signal Processing (ICASSP) , March 2016, pp. 2657–2661. [21] A. Zeyer, K. Irie, R. Schlter, and H. Ney, “Improved training of end-to-end attention models for speech recognition,” in Proc. Interspeech 2018 , 2018, pp. 7–11. [22] ...

---

In our study, we evaluate performance of models with:
• 3 types of normalization: batch norm [11], weight norm
[10], and layer norm [18]
• 3 types of rectiﬁed linear units: ReLU, clipped ReLU
(cReLU), and leaky ReLU (lReLU)
• 2 types of gated units: gated linear units (GLU) [9], and
gated activation units (GAU) [19]
All experiment results are shown in Table 2. We ﬁrst experi-
mented with a smaller Jasper5x3 3 model to pick the top 3 set-
tings before training on larger Jasper models. We found that
layer norm with GAU performed the best on the smaller model.
Layer norm with ReLU and batch norm with ReLU came sec-
ond and third in our tests. Using these 3, we conducted further
experiments on a larger Jasper10x4. For larger models, we no-
ticed that batch norm with ReLU outperformed other choices.
Thus, leading us to decide on batch normalization and ReLU
for our architecture.
During batching, all sequences are padded to match the
longest sequence. These padded values caused issues when us-
ing layer norm. We applied a sequence mask to exclude padding
values from the mean and variance calculation. Further, we
computed mean and variance over both the time dimension and
channels similar to the sequence-wise normalization proposed
by Laurent et al. [20]. In addition to masking layer norm, we
additionally applied masking prior to the convolution operation,
and masking the mean and variance calculations in batch norm.
These results are shown in Table 3. Interestingly, we found that
while masking before convolution gives a lower WER, using
masks for both convolutions and batch norm results in worse
performance.

---

the re-scaled gradient (as in AdamW [30]):
m l
t = β 1 · m l
t − 1 +
g l
t
p
v l
t + ϵ
+ d · w t
(3)
Finally, new weights are computed using the learning rate α t :
w t +1 = w t − α t · m t
(4)
Using NovoGrad instead of SGD with momentum, we de-
creased the WER on dev-clean LibriSpeech from 4.00% to
3.64%, a relative improvement of 9% for Jasper DR 10x5. For
more details and experiment results with NovoGrad, see [31].

---

For training, we use either Stochastic Gradient Descent (SGD)
with momentum or our own NovoGrad , an optimizer similar
to Adam [15], except that its second moments are computed
per layer instead of per weight. Compared to Adam, it reduces
memory consumption and we ﬁnd it to be more numerically
stable.
At each step t , NovoGrad computes the stochastic gradi-
ent g l
t following the regular forward-backward pass. Then the
second-order moment v l
t is computed for each layer l similar to
ND-Adam [29]:
v l
t = β 2 · v l
t − 1 + (1 − β 2 ) · || g l
t || 2
(1)
The second-order moment v l
t is used to re-scale gradients g l
t
before calculating the ﬁrst-order moment m l
t :
m l
t = β 1 · m l
t − 1 +
g l
t
p
v l
t + ϵ
(2)
Table 5: LibriSpeech, WER (%)
Model
E2E
LM
dev-clean
dev-other
test-clean
test-other
CAPIO (single) [23]
N
RNN
3.02
8.28
3.56
8.58
pFSMN-Chain [25]
N
RNN
2.56
7.47
2.97
7.5
DeepSpeech2 [26]
Y
5-gram
-
-
5.33
13.25
Deep bLSTM w/ attention [21]
Y
LSTM
3.54
11.52
3.82
12.76
wav2letter++ [27]
Y
ConvLM
3.16
10.05
3.44
11.24
LAS + SpecAugment 4 [28]
Y
RNN
-
-
2.5
5.8
Jasper DR 10x5
Y
-
3.64
11.89
3.86
11.95
Jasper DR 10x5
Y
6-gram
2.89
9.53
3.34
9.62
Jasper DR 10x5
Y
Transformer-XL
2.68
8.62
2.95
8.79
Jasper DR 10x5 + Time/Freq Masks 4
Y
Transformer-XL
2.62
7.61
2.84
7.84
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Only LibriSpeech table present; Hub5'00 baselines (LF-MMI, Seq2Seq, RNN-T, CTC...) are absent.

## CEC-10

**Question:** Is WordNet useful for taxonomic reasoning for this task?

**Reference answer(s):** Yes

<details><summary>Gold evidence</summary>

> While our methodology is amenable to any knowledge source and set of models/benchmark tasks, we focus on probing state-of-the-art transformer models BIBREF7, BIBREF9 in the domain of science MCQA. For sources of expert knowledge, we use WordNet, a comprehensive lexical ontology, and other publicly available dictionary resources. We devise probes that measure model competence in definition and taxonomic knowledge in different settings (including hypernymy, hyponymy, and synonymy detection, and word sense disambiguation). This choice is motivated by fact that the science domain is considered particularly challenging for QA BIBREF10, BIBREF11, BIBREF12, and existing science benchmarks are known to involve widespread use of such knowledge (see BIBREF1, BIBREF13 for analysis), which is also arguably fundamental to more complex forms of reasoning.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
owing to the provided contexts. WordNet is the most authoritative and widely- used knowledge resource in NLP, it also has the advantage of having mappings into other knowl- edge resources ( Niles and Pease , 2001 ; Navigli and Ponzetto , 2010 ; Tandon et al. , 2017 ), which allows for easily extending our probes to other do- mains and phenomena. Example Generation GEN ( τ ) . We build 4 indi- vidual datasets based on semantic relations native to WordNet: hypernymy (i.e., generalization or ISA reasoning up a taxonomy, ISA ↑ ), hyponymy (ISA ↓ ), synonymy , and definitions . To generate a set of questions in each case, we em- ploy a number of rule templates Q that operate over tuples. A subset of such templates is shown in Table 2 and were designed to mimic naturalis- tic (i.e., human authored) questions we observed in our science benchmarks. For example, suppose we wish to create a ques- tion q about the deﬁnition of a target concept c ∈C . We ﬁrst select a question template from Q that ﬁrst introduces the concept c and its lemma l ∈W in context using the example sentence con- text s ∈S , and then asks to identify the corre- sponding WordNet gloss d ∈D , which serves as the gold answer a . The same is done for ISA rea- soning; each question about a hypernym/hyponym relation between two concepts c → ↑ / ↓ c ′ ∈T i (e.g., dog → ↑ / ↓ animal/terrier ) ﬁrst intro- duces a context for c and then asks for an answer that identiﬁes c ′ (which is also provided with a gloss so as to contain all available context). in Table 2 cover only direct ISA links from c in

---

to construct gold question-answer pairs ( q , a ) from a triple graph G . low, we also provide estimates of human perfor- mance on our test sets, and in some cases intro- duce smaller gold-standard test sets to allow for a direct comparison with model performance. WordNet is a publicly-available English lexical database consisting of around 117k concepts, which are organized into groups of synsets that each contain a gloss (i.e., a deﬁnition), a set of rep- resentative English words (called lemmas ), and, in around 33k synsets, example sentences. In addi- tion, many synsets have ISA links to other synsets that express complex taxonomic relations. Fig- ure 2 shows an example and Table 1 summarizes how we formulate WordNet as a set of triples T of various types. These triples together represent a directed, edge-labeled graph G . Our main motivation for using WordNet, as op- posed to a resource such as ConceptNet ( Havasi et al. , 2007 ), is the availability of glosses ( D ) and example sentences ( S ), which allows us to con- struct natural language questions that contextual- ize the types of concepts we want to probe. For ex- ample, when probing whether a model has knowl- edge of a concept such as bank (a ﬁnancial institu- tion), we provide an example sentence he cashed a check at the bank , to help disambiguate the par- ticular sense of bank we are probing. Sentential contexts also provide additional hints to models in cases of rare or infrequent concepts. 5 Since probed concepts may have explicitly been observed during QA training. Nevertheless, unlike prior probing studies ( Petroni et al. , 2019 ), we did not see a substantial perfor- mance disparity between observed and unobserved concepts across our models, perhaps

---

each model to become informed about the format of each probe. We also explore a more complex set of probing templates. The use of lexical resources such as WordNet to construct datasets has a long history, and has re- cently appeared in work on adversarial attacks ( Jia and Liang , 2017 ) and general task construction ( Pilehvar and Camacho-Collados , 2019 ). In the area of MCQA, there is related work on construct- ing questions from tuples ( Jauhar et al. , 2016 ; Tal- mor et al. , 2019b ), both of which involve standard crowd annotation to elicit question-answer pairs (see also Seyler et al. ( 2017 ); Reddy et al. ( 2017 )). In contrast to this work, we focus on generating data in an entirely automatic and silver-standard fashion (i.e., in a way that potentially introduces a little noise), which obviates the need for expensive annotation and gives us the ﬂexibility to construct much larger datasets that control a rich set of se- mantic aspects of the target questions. Following standard practices in MCQA dataset creation (e.g., Khot et al. , 2020 ), however, we perform crowd- sourcing to obtain conservative (in the sense of Nangia and Bowman ( 2019 )) estimates of human performance on our main evaluation sets, to com- pare against model performance. While our probing methodology is amenable to any domain, we focus on probing open-domain Set WordNet (WN) GCIDE R {isa ↑ ,isa ↓ , {def, ex, lemma} def, ex, lemma} C { WN synsets } { entry ids } D { synset glosses } { unique defs } S { synset sentences } { entry examples } W { synset lemmas } { all words } Atomic Triple Types Deﬁnition Concept Senses and Deﬁnitions T d ⊆ {def}

---

each unique entry to be a distinct sense. Our probe centers around word-sense disambiguation. To buildQA examples, we use the same gener- ation templates for deﬁnitions exempliﬁed in Ta- ble 2 for WordNetQA. To construct distractors, we simply take alternative deﬁnitions for the target words that represent a different word sense (e.g., the alternative deﬁnitions of gift in Table 5 ), and randomly chosen deﬁnitions if needed to create a 5-way multiple choice question. As above, we re- serve a maximum of 3k examples for training, and use the same amount for development. Our initial attempts at building this dataset via standard random splitting resulted in certain systematic biases, revealed by high performance of the choice-only model we used as a control. Among other factors, we found the use of deﬁni- tions from entries without example sentences as distractors (see again Table 5 ) to have a surprising correlation with such biases. Filtering such dis- tractors helped improve the quality of this probe. For assessing human performance, we anno- tated a smaller gold-standard test set consisting of around 1,100 questions using the crowd-sourcing elicitation setup described in Section 3.1 . Given the probes above, we now can start to an- swer the empirical questions posed at the begin- ning. Our main focus is on looking at transformer- based MCQA models trained on science bench- marks in Table 6 . We start with our target MCQA models, as well as several control baselines. 4.1 Task Deﬁnition and Modeling Given a dataset D = { ( q ( d ) , { a ( d ) N } ) } | D | d consisting of pairs of questions stems q and an- swer choices a i , the goal is to ﬁnd the correct an- swer a i ∗ that correctly
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Context shows WordNet ISA/hypernymy relations used to build taxonomic probes.

## CEC-11

**Question:** What is the model performance on target language reading comprehension?

**Reference answer(s):** Table TABREF6 | Table TABREF8 ‖ when testing on English, the F1 score of the model training on Chinese (Zh) is 53.8 |  F1 score is only 44.1 for the model training on Zh-En

<details><summary>Gold evidence</summary>

> Table TABREF6 shows the result of different models trained on either Chinese or English and tested on Chinese. In row (f), multi-BERT is fine-tuned on English but tested on Chinese, which achieves competitive performance compared with QANet trained on Chinese. We also find that multi-BERT trained on English has relatively lower EM compared with the model with comparable F1 scores. This shows that the model learned with zero-shot can roughly identify the answer spans in context but less accurate. In row (c), we fine-tuned a BERT model pre-trained on English monolingual corpus (English BERT) on Chinese RC training data directly by appending fastText-initialized Chinese word embeddings to the original word embeddings of English-BERT. Its F1 score is even lower than that of zero-shot transferring multi-BERT (rows (c) v.s. (e)). The result implies multi-BERT does acquire better cross-lingual capability through pre-training on multilingual corpus. Table TABREF8 shows the results of multi-BERT fine-tuned on different languages and then tested on English , Chinese and Korean. The top half of the table shows the results of training data without translation. It is not surprising that when the training and testing sets are in the same language, the best results are achieved, and multi-BERT shows transfer capability when training and testing sets are in different languages, especially between Chinese and Korean.
> In the lower half of Table TABREF8, the results are obtained by the translated training data. First, we found that when testing on English and Chinese, translation always degrades the performance (En v.s. En-XX, Zh v.s. Zh-XX). Even though we translate the training data into the same language as testing data, using the untranslated data still yield better results. For example, when testing on English, the F1 score of the model training on Chinese (Zh) is 53.8, while the F1 score is only 44.1 for the model training on Zh-En. This shows that translation degrades the quality of data. There are some exceptions when testing on Korean. Translating the English training data into Chinese, Japanese and Korean still improve the performance on Korean. We also found that when translated into the same language, the English training data is always better than the Chinese data (En-XX v.s. Zh-XX), with only one exception (En-Fr v.s. Zh-Fr when testing on KorQuAD). This may be because we have less Chinese training data than English. These results show that the quality and the size of dataset are much more important than whether the training and testing are in the same language or not.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Reading Comprehension (RC) has become a
central task in natural language processing, with
great practical value in various industries.
In
recent years, many large-scale RC datasets in
English
( Hermann et al. ,
2015 ;
Hewlett et al. ,
2016 ;
Rajpurkar et al. ,
2016 ;
Nguyen et al. ,
2016 ; Trischler et al. , 2017 ; Joshi et al. , 2017 ;
Rajpurkar et al. ,
2018 )
have
nourished
the
development
of
numerous
powerful
and di-
verse RC models
( Seo et al. , 2016 ; Hu et al. ,
2018 ;
Wang et al. ,
2017 ;
Clark and Gardner ,
2018 ; Huang et al. , 2017 ).
The state-of-the-art
model ( Devlin et al. , 2018 ) on SQuAD, one of the
most widely used RC benchmarks, even surpasses
human-level performance.
Nonetheless, RC on
languages other than English has been limited
due to the absence of sufﬁcient training data. Al-
though some efforts have been made to create RC
datasets for Chinese ( He et al. , 2018 ; Shao et al. ,
2018 ) and Korean ( Seungyoung Lim , 2018 ), it
is not feasible to collect RC datasets for every
∗ Equal contribution
0 All the modiﬁcations of existing corpora used in this
paper would be released in https://github.com/ntu-spml-
lab/artiﬁcial-reading-comprehension-datasets
language since annotation efforts to collect a new
RC dataset are often far from trivial. Therefore,
the setup of transfer learning, especially zero-shot
learning, is of extraordinary importance.
Existing methods ( Asai et al. , 2018 ) of cross-
lingual transfer learning on RC datasets often
count on machine translation (MT) to translate
data from source language into target language,

---

Kr: Korean, xx-yy: translated from xx to yy). The text
in bold means training data language is the same as test-
ing data language.
trained on English has relatively lower EM com-
pared with the model with comparable F1 scores.
This shows that the model learned with zero-shot
can roughly identify the answer spans in con-
text but less accurate. In row (c), we ﬁne-tuned
a BERT model pre-trained on English monolin-
gual corpus (English BERT) on Chinese RC train-
ing data directly by appending fastText-initialized
Chinese word embeddings to the original word
embeddings of English-BERT. Its F1 score is even
lower than that of zero-shot transferring multi-
BERT (rows (c) v.s. (e)). The result implies multi-
BERT does acquire better cross-lingual capability
through pre-training on multilingual corpus.
Table 2 shows the results of multi-BERT ﬁne-
tuned on different languages and then tested on
English , Chinese and Korean. The top half of
the table shows the results of training data without
translation. It is not surprising that when the train-
ing and testing sets are in the same language, the
best results are achieved, and multi-BERT shows
transfer capability when training and testing sets
are in different languages, especially between Chi-
nese and Korean.
In the lower half of Table 2 , the results are ob-
tained by the translated training data. First, we
found that when testing on English and Chinese,
translation always degrades the performance (En
v.s.
En-XX, Zh v.s.
Zh-XX). Even though we
translate the training data into the same language

---

It has been shown that extractive QA tasks like
SQuAD may be tackled by some language inde-
pendent strategies, for example, matching words
in questions
and
context
( Weissenborn et al. ,
2017 ). Is zero-shot learning feasible because the
model simply learns this kind of language inde-
pendent strategies on one language and apply to
the other?
To verify whether multi-BERT largely counts
on a language independent strategy,
we test
the model on the languages unseen during pre-
training. To make sure the languages have never
been seen before, we artiﬁcially make unseen lan-
guages by permuting the whole vocabulary of ex-
isting languages.
That is, all the words in the
sentences of a speciﬁc language are replaced by
other words in the same language to form the sen-
tences in the created unseen language. It is as-
sumed that if multi-BERT used to ﬁnd answers by
language independent strategy, then multi-BERT
should also do well on unseen languages. Table 4
shows that the performance of multi-BERT drops
drastically on the dataset. It implies that multi-
BERT might not totally rely on pattern matching
when ﬁnding answers.
(a) Before Fine-tuning
(b) After Fine-tuning
Figure 1: PCA visualization of hidden representations
from the 12-th transformer layer of multi-BERT before
and after ﬁne-tuning on English. The red points rep-
resent Chinese tokens, and the blue points are for En-
glish.

---

Because it is not feasible to collect training
data for every language, there is a growing
interest in cross-lingual transfer learning. In
this paper, we systematically explore zero-
shot cross-lingual transfer learning on reading
comprehension tasks with a language repre-
sentation model pre-trained on multi-lingual
corpus.
The experimental results show that
with pre-trained language representation zero-
shot learning is feasible, and translating the
source data into the target language is not nec-
essary and even degrades the performance. We
further explore what does the model learn in
zero-shot setting 0 .

---

Table 2 shows that ﬁne-tuning on un-translated
target language data achieves much better per-
formance than data translated into the target lan-
guage. Because the above statement is true across
all the languages, it is a strong evidence that trans-
lation degrades the performance.We notice that the
translated corpus and untranslated corpus are not
the same. This may be another factor that inﬂu-
ences the results. Conducting an experiment be-
tween un-translated and back-translated data may
deal with this problem.
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Only qualitative discussion; table numbers and the 53.8 vs 44.1 sentence are cut off.

## CEC-12

**Question:** What evaluation criteria and metrics were used to evaluate the generated text?

**Reference answer(s):** BLEU  | NIST  | METEOR  | ROUGE-L | CIDEr  | evaluation script | automatic evaluation | human evaluation | minimum edit evaluation | word error rate (WER) | factual errors and their types | fluency issues | acceptability of the output for production use in a news agency ‖ BLEU | NIST | METEOR | ROUGE-L | CIDEr

<details><summary>Gold evidence</summary>

> In Table TABREF15 we measure BLEU BIBREF19, NIST BIBREF20, METEOR BIBREF21, ROUGE-L BIBREF22 and CIDEr BIBREF23 metrics on the 2018 E2E NLG Challenge test data using the evaluation script provided by the organizers. Our generation system is compared to the official shared task baseline system, TGen BIBREF24, as well as to the top performing participant system on each score (ST top). Our system outperforms the TGen baseline on 3 out of 5 metrics (BLEU, METEOR and ROUGE-L), which is on par with the official shared task results, where not a single one participant system was able to surpass the baseline on all five metrics. On two metrics, BLEU and METEOR, our system outperforms the best shared task participants.
> Our alignment serves as a gold standard reflecting which events the journalists have chosen to mention for each game. In our generation task, we are presented with the problem of selecting appropriate events from the full game statistics. We use the gold standard selection during training and validation of the text generation model, as well as the automatic evaluation. As we deploy our text generation model for manual evaluation, we use a Conditional Random Field (CRF) model to predict which events to mention.
> The second human evaluation aimed at judging the acceptability of the output for production use in a news agency. The output is evaluated in terms of its usability for a news channel labelled as being machine-generated, i.e. not aiming at the level of a human journalist equipped with substantial background information. The evaluation was carried out by two journalists from the STT agency, who split the 59 games among themselves approximately evenly. The first journalist edited the games to a form corresponding to a draft for subsequent minor post-editing by a human, simulating the use of the generated output as a product where the final customer is expected to do own post-editing before publication. The second journalist directly edited the news to a state ready for direct publication in a news stream labeled as machine-generated news. In addition to correcting factual errors, the journalists removed excessive repetition, improved text fluency, as well as occasionally included important facts which the system left ungenerated. The WER measured against the output considered ready for post-editing, is 9.9% (11.2% disregarding punctuation), only slightly worse than the evaluation with only the factual and grammatical errors corrected. The WER measured against the output considered ready for direct release, was 22.0% (24.4% disregarding punctuation). In other words, 75–90% of the generated text can be directly used, depending on the expected post-editing effort.
> In the minimum edit evaluation, carried out by the annotator who created the news corpus, only factual mistakes and grammatical errors are corrected, resulting in text which may remain awkward or unfluent. The word error rate (WER) of the generated text compared to its corrected variant as a reference is 5.6% (6.2% disregarding punctuation). The WER measure is defined as the number of insertions, substitutions, and deletions divided by the total length of the reference, in terms of tokens. The measure is the edit distance of the generated text and its corrected variant, directly reflecting the amount of effort needed to correct the generated output.
> The factual errors and their types are summarized in Table TABREF23. From the total of 510 game events generated by the system, 78 of these contained a factual error, i.e. 84.7% were generated without factual errors.
> Most fluency issues relate to the overall flow and structure of the report. Addressing these issues would require the model to take into account multiple events in a game, and combine the information more flexibly to avoid repetition. For instance, the output may repeatedly mention the period number for all goals in the same period. Likewise, this setup sometimes results in unnatural, yet grammatical, repetition of words across consecutive sentences. Even though the model has learned a selection of verbs meaning to score a goal, it is unable to ensure their varied use. While not successful in our initial experiments, generating text based on the multi-event alignments or at document level may eventually overcome these issues.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Generation
In Table 4, we provide evaluation results using the
ﬁve aforementioned metrics. We evaluate on event
level using gold standard event selection, where
each generated event description is compared to
its existing reference text. As the model is trained
to produce a tokenized sequence, we apply a deto-
kenizer to be able to compare against the origi-
nal untokenized reference text. On the test set,
the model achieves a BLEU score of 19.67. To
the extent that different datasets allow comparison,
the best reported score on the Rotowire basketball
news corpus is 16.50 (Puduppully et al., 2019).
Compared to our earlier E2E baseline experiment,
we score lower than our closest comparable ref-
erence of 31.90 (with single references), which is
understandable due to the much smaller train set
size for the hockey corpus (about 13% in size).
In Figure 3, we plot the learning curve with in-
creasing sizes of training data in order to illustrate
how generation performance beneﬁts from more
data. The learning curve is still steadily increas-
ing when using 100% of the training data currently
available, which indicates that more data would
most likely further improve the performance.
INPUT:
<length>long</length> <type>result</type> <home> ¨ Ass¨at </home> <guest> Blues </guest>
<score> 0 - 4 </score> <periods> ( 0 - 3 , 0 - 0 , 0 - 1 ) </periods>
OUTPUT:
Blues vei voiton ¨ Assist¨a maalein 4 - 0 ( 3 - 0 , 0 - 0 , 1 - 0 ) .
Figure 2: An example input–output pair for the text generation model, derived from manual alignment.
The original, untokenized output sentence is Blues vei voiton ¨ Assist¨a maalein 4–0 (3–0, 0–0, 1–0).
(Literal English translation: Blues took a win from ¨ Ass¨at with goals 4–0 (3–0, 0–0, 1–0). )
BLEU
0.1967
NIST
4.4144
METEOR
0.2297
ROUGE-L
0.4159
CIDEr
1.8658
Table 4: Automatic evaluation metrics on hockey
corpus test set.
Figure 3: Learning curve demonstrating the effect
of training data size on generation performance.

---

The second human evaluation aimed at judging
the acceptability of the output for production use
in a news agency.
The output is evaluated in
terms of its usability for a news channel labelled
as being machine-generated, i.e. not aiming at the
level of a human journalist equipped with sub-
stantial background information. The evaluation
was carried out by two journalists from the STT
agency, who split the 59 games among themselves
approximately evenly. The ﬁrst journalist edited
the games to a form corresponding to a draft for
subsequent minor post-editing by a human, simu-
lating the use of the generated output as a prod-
uct where the ﬁnal customer is expected to do
own post-editing before publication. The second
journalist directly edited the news to a state ready
for direct publication in a news stream labeled as
machine-generated news. In addition to correcting
factual errors, the journalists removed excessive
repetition, improved text ﬂuency, as well as occa-
sionally included important facts which the system
left ungenerated. The WER measured against the
output considered ready for post-editing, is 9.9%
(11.2% disregarding punctuation), only slightly
worse than the evaluation with only the factual and
grammatical errors corrected. The WER measured
against the output considered ready for direct re-
lease, was 22.0% (24.4% disregarding punctua-
tion). In other words, 75–90% of the generated
text can be directly used, depending on the ex-
pected post-editing effort.
Figure 4 shows two example games along
with the generated reports and manual corrections
made by the journalist in order to prepare it for
publication. Literal translations from the gener-
ated, uncorrected Finnish into English are pro-
vided for reference.

---

As our objective is practically usable news gen-
eration, we carry out a manual evaluation of its
output on 59 randomly selected games from the
test set, focusing in particular on the corrections
that would be necessary to obtain acceptable out-
put. Example corrections are shown in Figure 4.
These full game reports are generated by ﬁrst ap-
plying the selection model described in Section 3
to select the events to be included in the report,
and then using the text generation model to ver-
balize each selected event. The generated texts of
the events are then detokenized and concatenated
in chronological order into a full game report.

---

Next, we present the model architecture used in
text generation, and evaluate the model on a pop-

---

Regina Barzilay and Mirella Lapata. 2005. Collective
content selection for concept-to-text generation. In
Proceedings of Human Language Technology Con-
ference and Conference on Empirical Methods in
Natural Language Processing , pages 331–338, Van-
couver, British Columbia, Canada. Association for
Computational Linguistics.
Alberto Costa and Giacomo Nannicini. 2014. RBFOpt:
an open-source library for black-box optimization
with costly function evaluations. Optimization On-
line , 4538.
George Doddington. 2002.
Automatic evaluation
of machine translation quality using n-gram co-
occurrence statistics.
In Proceedings of the Sec-
ond International Conference on Human Lan-
guage Technology Research , pages 138–145. Mor-
gan Kaufmann Publishers Inc.
Ondˇrej Duˇsek and Filip Jurˇc´ıˇcek. 2016. Sequence-to-
sequence generation for spoken dialogue via deep
syntax trees and strings. In Proceedings of the 54th
Annual Meeting of the Association for Computa-
tional Linguistics (Volume 2: Short Papers) , pages
45–51, Berlin, Germany. Association for Computa-
tional Linguistics.
Ondˇrej Duˇsek, Jekaterina Novikova, and Verena Rieser.
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) BLEU/NIST/METEOR/ROUGE-L/CIDEr table plus human eval (WER, acceptability) present.

## CEC-13

**Question:** Do they evaluate only on English datasets?

**Reference answer(s):** Yes

<details><summary>Gold evidence</summary>

> For both POS tagging and dependency parsing, we run experiments on the Wall Street Journal (WSJ) portion of the Penn Treebank. To create the observed data embeddings, we train skip-gram word embeddings BIBREF7 that are found to capture syntactic properties well when trained with small context window BIBREF8 , BIBREF9 . Following BIBREF9 , the dimensionality INLINEFORM0 is set to 100, and the training context window size is set to 1 to encode more syntactic information. The skip-gram embeddings are trained on the one billion word language modeling benchmark dataset BIBREF21 in addition to the WSJ corpus.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
by running top performing systems using our more difﬁcult
training setup when this was feasible – but it was not possible
to evaluate them all.
System
M-1
VM
Gaussian HMM
72.0
65.0
Ours (4 layers)
76.4
69.3
Ours (8 layers)
76.8
69.4
Ours (16 layers)
67.3
62.0
Table 4 : Unsupervised POS tagging results on WSJ, with
fastText vectors as the observed embeddings.
System
⩽ 10
all
Gaussian DMV
53.6
41.3
Ours (4 layers)
56.9
43.9
Ours (8 layers)
57.1
42.3
Ours (16 layers)
52.9
39.5
Table 5 : Directed dependency accuracy on section 23 of
WSJ, with fastText vectors as the observed embeddings.
ging experiments, our parsing model seems to be
quite sensitive to the initialization. For example,
directed accuracy of our approach on sentences of
length ⩽ 10 is below 40.0 with random initializa-
tion. This is consistent with previous work that has
noted the importance of careful initialization for
DMV-based models such as the commonly used
harmonic initializer ( Klein and Manning , 2004 ).
However, it is not straightforward to apply the har-
monic initializer for DMV directly in our model
without using some kind of pre-training since we
do not observe gold POS.
Impact of Observed Embeddings.
We investi-
gate the effect of the choice of pre-trained embed-
ding on performance while using our approach.
To this end, we additionally include results us-
ing fastText embeddings ( Bojanowski et al. , 2017 )
– which, in contrast with skip-gram embeddings,
include character-level information.
We set the
context windows size to 1 and the dimension size
to 100 as in the skip-gram training, while keep-
ing other parameters set to their defaults. These
results are summarized in Table 4 and Table 5 .
While fastText embeddings lead to reduced perfor-
mance with our model, our approach still yields an
improvement over the Gaussian baseline with the
new observed embeddings space.

---

In this section, we ﬁrst describe our datasets and
experimental setup. We then instantiate our ap-
proach with Markov and DMV-structured syntax
models, and report results on POS tagging and de-
pendency grammar induction respectively. Lastly,
we analyze the learned latent embeddings.

---

Wiley & Sons. J¨orn-Henrik Jacobsen, Arnold Smeulders, and Edouard Oyallon. 2018. i-revnet: Deep invertible networks. arXiv preprint arXiv:1802.07088 . Yong Jiang, Wenjuan Han, and Kewei Tu. 2016. Unsu- pervised neural dependency parsing. In Proceedings of EMNLP . Mark Johnson. 2007. Why doesnt em ﬁnd good hmm pos-taggers? In Proceedings of the EMNLP- CoNLL . Diederik P Kingma and Jimmy Ba. 2014. Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980 . Diederik P Kingma and Prafulla Dhariwal. 2018. Glow: Generative ﬂow with invertible 1x1 convo- lutions. arXiv preprint arXiv:1807.03039 . Diederik P Kingma, Tim Salimans, Rafal Jozefowicz, Xi Chen, Ilya Sutskever, and Max Welling. 2016. Improved variational inference with inverse autore- gressive ﬂow. In Advances in Neural Information Processing Systems , pages 4743–4751.
Diederik P Kingma and Max Welling. 2013.
Auto-
encoding
variational
bayes.
arXiv
preprint
arXiv:1312.6114 .
Dan Klein and Christopher D Manning. 2004. Corpus-
based induction of syntactic structure: Models of de-
pendency and constituency. In Proceedings of ACL .
Phong Le and Willem Zuidema. 2015. Unsupervised
dependency parsing: Let’s use supervised parsers.
In Proceedings of NAACL-HLT .
Omer Levy and Yoav Goldberg. 2014. Dependency-
based word embeddings. In Proceedings of ACL .
Chu-Cheng Lin, Waleed Ammar, Chris Dyer, and Lori
Levin. 2015. Unsupervised pos induction with word
embeddings. In Proceedings of the NAACL-HLT .
Laurens van der Maaten and Geoffrey Hinton. 2008.
Visualizing data using t-sne.
Journal of Machine
Learning Research .
Mitchell P Marcus, Mary Ann Marcinkiewicz, and
Beatrice Santorini. 1993. Building a large annotated
corpus of english: The penn treebank.
Computa-
tional linguistics , 19(2):313–330.
Yishu Miao and Phil Blunsom. 2016. Language as a
latent variable: Discrete generative models for sen- tence compression. In Proceedings of EMNLP . Tomas Mikolov, Kai Chen, Greg Corrado, and Jef- frey Dean. 2013. Efﬁcient estimation of word representations in vector space. arXiv preprint arXiv:1301.3781 . John K Pate and Sharon Goldwater. 2013. Unsu- pervised dependency parsing with acoustic cues. Transactions of the Association for Computational Linguistics . John K Pate and Mark Johnson. 2016. Grammar in- duction from (lots of) words alone. In Proceedings of COLING . Matthew E Peters, Mark Neumann, Mohit Iyyer, Matt Gardner, Christopher Clark, Kenton Lee, and Luke Zettlemoyer. 2018. Deep contextualized word rep- resentations. In Proceedings of HLT-NAACL . Danilo Jimenez Rezende and Shakir Mohamed. 2015. Variational inference with normalizing ﬂows. In Proceedings of ICML . Andrew Rosenberg and Julia Hirschberg. 2007. V- measure: A conditional entropy-based external clus- ter evaluation measure. In Proceedings of EMNLP- CoNLL . Valentin I Spitkovsky, Hiyan Alshawi, Angel X Chang, and Daniel Jurafsky. 2011a. Unsupervised depen- dency parsing without gold part-of-speech tags. In Proceedings of EMNLP . Valentin I Spitkovsky, Hiyan Alshawi, and Daniel Ju- rafsky. 2011b. Punctuation: Making a point in un- supervised dependency parsing. In Proceedings of CoNLL . Valentin I Spitkovsky, Hiyan Alshawi, and Daniel ...
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) POS tagging and parsing results both on WSJ (Penn Treebank, English).

## CEC-14

**Question:** What evaluation metrics are looked at for classification tasks?

**Reference answer(s):** Precision | Recall | F-measure | accuracy ‖ Precision, Recall and F-measure

<details><summary>Gold evidence</summary>

> Precision, Recall and F-measure for this multi-label classification are computed using a strategy similar to the one described in BIBREF21 . Let INLINEFORM0 be the set of predicted labels and INLINEFORM1 be the set of actual labels for the INLINEFORM2 instance. Precision and recall for this instance are computed as follows: INLINEFORM3
> We randomly selected 2000 sentences from the supervisor assessment corpus and manually tagged them (dataset D1). This labelled dataset contained 705, 103, 822 and 370 sentences having the class labels STRENGTH, WEAKNESS, SUGGESTION or OTHER respectively. We trained several multi-class classifiers on this dataset. Table TABREF10 shows the results of 5-fold cross-validation experiments on dataset D1. For the first 5 classifiers, we used their implementation from the SciKit Learn library in Python (scikit-learn.org). The features used for these classifiers were simply the sentence words along with their frequencies. For the last 2 classifiers (in Table TABREF10 ), we used our own implementation. The overall accuracy for a classifier is defined as INLINEFORM0 , where the denominator is 2000 for dataset D1. Note that the pattern-based approach is unsupervised i.e., it did not use any training data. Hence, the results shown for it are for the entire dataset and not based on cross-validation.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
In this paper, we presented an analysis of the text generated in Performance
Appraisal (PA) process in a large multi-national IT company. We performed
sentence classiﬁcation to identify strengths, weaknesses and suggestions for im-
provements found in the supervisor assessments and then used clustering to
discover broad categories among them. As this is non-topical classiﬁcation, we
found that SVM with ADWS kernel [16] produced the best results. We also used
multi-class multi-label classiﬁcation techniques to match supervisor assessments
to predeﬁned broad perspectives on performance. Logistic Regression classiﬁer
was observed to produce the best results for this topical classiﬁcation. Finally,
we proposed an ILP-based summarization technique to produce a summary of
peer feedback comments for a given employee and compared it with manual
summaries.
The PA process also generates much structured data, such as supervisor
ratings. It is an interesting problem to compare and combine the insights from
discovered from structured data and unstructured text. Also, we are planning
to automatically discover any additional performance attributes to the list of 15
attributes currently used by HR.

---

and suggestions of improvements found in the supervisor assessments?
2. For my workforce, how many supervisor comments are present for each of
a given ﬁxed set of perspectives (which we call attributes ), such as FUNC-
TIONAL
EXCELLENCE ,
CUSTOMER
FOCUS ,
BUILDING
EFFECTIVE
TEAMS
etc.?
3. What is the summary of the peer feedback for a given employee?
In this paper, we develop text mining techniques that can automatically produce
answers to these questions. Since the intended users are HR executives, ideally,
the techniques should work with minimum training data and experimentation
with parameter setting. These techniques have been implemented and are being
used in a PA system in a large multi-national IT company.
The rest of the paper is organized as follows. Section 2 summarizes related
work. Section 3 summarizes the PA dataset used in this paper. Section 4 ap-
plies sentence classiﬁcation algorithms to automatically discover three impor-
tant classes of sentences in the PA corpus viz., sentences that discuss strengths,
weaknesses of employees and contain suggestions for improving her performance.
Section 5 considers the problem of mapping the actual targets mentioned in
strengths, weaknesses and suggestions to a ﬁxed set of attributes. In Section 6,
we discuss how the feedback from peers for a particular employee can be sum-
marized. In Section 7 we draw conclusions and identify some further work.

---

arXiv:1712.00991v1  [cs.CL]  4 Dec 2017
Mining Supervisor Evaluation and Peer
Feedback in Performance Appraisals
Girish Keshav Palshikar, Sachin Pawar, Saheb Chourasia, Nitin Ramrakhiyani
TCS Research, Tata Consultancy Services Limited,
54B Hadapsar Industrial Estate, Pune 411013, India.
{ gk.palshikar, sachin7.p, saheb.c, nitin.ramrakhiyani } @tcs.com
Abstract. Performance appraisal (PA) is an important HR process to
periodically measure and evaluate every employee’s performance vis-a-
vis the goals established by the organization. A PA process involves pur-
poseful multi-step multi-modal communication between employees, their
supervisors and their peers, such as self-appraisal, supervisor assessment
and peer feedback. Analysis of the structured data and text produced
in PA is crucial for measuring the quality of appraisals and tracking
actual improvements. In this paper, we apply text mining techniques
to produce insights from PA text. First, we perform sentence classiﬁca-
tion to identify strengths, weaknesses and suggestions of improvements
found in the supervisor assessments and then use clustering to discover
broad categories among them. Next we use multi-class multi-label classi-
ﬁcation techniques to match supervisor assessments to predeﬁned broad
perspectives on performance. Finally, we propose a short-text summa-
rization technique to produce a summary of peer feedback comments
for a given employee and compare it with manual summaries. All tech-
niques are illustrated using a real-life dataset of supervisor assessment
and peer feedback text produced during the PA of 4528 employees in a
large multi-national IT company.

---

We also explored whether a sentiment analyzer can be used as a baseline for
identifying the class labels STRENGTH and WEAKNESS . We used an implemen-
tation of sentiment analyzer from TextBlob 1 to get a polarity score for each
sentence. Table 2 shows the distribution of positive, negative and neutral sen-
timents across the 3 class labels STRENGTH , WEAKNESS and SUGGESTION . It
can be observed that distribution of positive and negative sentiments is almost
similar in STRENGTH as well as SUGGESTION sentences, hence we can conclude
that the information about sentiments is not much useful for our classiﬁcation
problem.

---

In many organizations, PA is done from a predeﬁned set of perspectives, which we
call attributes . Each attribute covers one speciﬁc aspect of the work done by the
employees. This has the advantage that we can easily compare the performance
of any two employees (or groups of employees) along any given attribute. We
can correlate various performance attributes and ﬁnd dependencies among them.
We can also cluster employees in the workforce using their supervisor ratings
for each attribute to discover interesting insights into the workforce. The HR
managers in the organization considered in this paper have deﬁned 15 attributes
(Table 6). Each attribute is essentially a work item or work category described
at an abstract level. For example, FUNCTIONAL
EXCELLENCE covers any tasks,
goals or activities related to the software engineering life-cycle (e.g., requirements
analysis, design, coding, testing etc.) as well as technologies such as databases,
web services and GUI.
In the example in Section 4, the ﬁrst sentence (which has class STRENGTH )
can be mapped to two attributes: FUNCTIONAL
EXCELLENCE and BUILD-
ING
EFFECTIVE
TEAMS . Similarly, the third sentence (which has class WEAK-
NESS ) can be mapped to the attribute INTERPERSONAL
EFFECTIVENESS and so
forth. Thus, in order to answer the second question in Section 1, we need to map
each sentence in each of the 3 classes to zero, one, two or more attributes, which
is a multi-class multi-label classiﬁcation problem.
We manually tagged the same 2000 sentences in Dataset D1 with attributes,
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) No mention of precision/recall/F-measure/accuracy in context.

## CEC-15

**Question:** What is te core component for KBQA?

**Reference answer(s):** answer questions by obtaining information from KB tuples  ‖ hierarchical matching between questions and relations with residual learning

<details><summary>Gold evidence</summary>

> Knowledge Base Question Answering (KBQA) systems answer questions by obtaining information from KB tuples BIBREF0 , BIBREF1 , BIBREF2 , BIBREF3 , BIBREF4 , BIBREF5 . For an input question, these systems typically generate a KB query, which can be executed to retrieve the answers from a KB. Figure 1 illustrates the process used to parse two sample questions in a KBQA system: (a) a single-relation question, which can be answered with a single $<$ head-entity, relation, tail-entity $>$ KB tuple BIBREF6 , BIBREF7 , BIBREF2 ; and (b) a more complex case, where some constraints need to be handled for multiple entities in the question. The KBQA system in the figure performs two key tasks: (1) entity linking, which links $n$ -grams in questions to KB entities, and (2) relation detection, which identifies the KB relation(s) a question refers to.
> Our main contributions include: (i) An improved relation detection model by hierarchical matching between questions and relations with residual learning; (ii) We demonstrate that the improved relation detector enables our simple KBQA system to achieve state-of-the-art results on both single-relation and multi-relation KBQA tasks.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
makes the model training easier and results in more abstract (deeper) question rep- resentations, thus improves hierarchical matching. relation detection could beneﬁt the KBQA end task, we also propose a simple KBQA implemen- tation composed of two-step relation detection . Given an input question and a set of candidate enti- ties retrieved by an entity linker based on the ques- tion, our proposed relation detection model plays a key role in the KBQA process: (1) Re-ranking the entity candidates according to whether they con- nect to high conﬁdent relations detected from the raw question text by the relation detection model. This step is important to deal with the ambigui- ties normally present in entity linking results. (2) Finding the core relation (chains) for each topic entity 2 selection from a much smaller candidate entity set after re-ranking. The above steps are followed by an optional constraint detection step, when the question cannot be answered by single relations (e.g., multiple entities in the question). Finally the highest scored query from the above the root of the (directed) query tree; and core-chain is the directed path of relation from root to the answer node. steps is used to query the KB for answers. Our main contributions include: (i) An im- proved relation detection model by hierarchical matching between questions and relations with residual learning; (ii) We demonstrate that the im- proved relation detector enables our simple KBQA system to achieve state-of-the-art results on both single-relation and multi-relation KBQA tasks. Relation Extraction Relation extraction (RE) is an important sub-ﬁeld of information extraction. General research in this ﬁeld usually works on a (small) pre-deﬁned relation set, where given a text paragraph and two target entities, the goal is to determine whether the text indicates any types of relations between the entities or not. As

---

different rela- tion detection models on the KBQA end-task, we also implemented another baseline that uses our KBQA system but replaces HR-BiLSTM with our implementation of AMPCNN (for SimpleQues- tions) or the char-3-gram BiCNN (for WebQSP) relation detectors (second block in Table 3). Compared to the baseline relation detector (3rd row of results), our method, which includes an im- proved relation detector (HR-BiLSTM), improves the KBQA end task by 2-3% (4th row). Note that in contrast to previous KBQA systems, our sys- tem does not use joint-inference or feature-based re-ranking step, nevertheless it still achieves better or comparable results to the state-of-the-art. The third block of the table details two ablation tests for the proposed components in our KBQA systems: (1) Removing the entity re-ranking step signiﬁcantly decreases the scores. Since the re- ranking step relies on the relation detection mod- els, this shows that our HR-BiLSTM model con- tributes to the good performance in multiple ways. 11 The STAGG score on SQ is from (Bao et al., 2016). Accuracy System SQ WQ STAGG 72.8 63.9 AMPCNN (Yin et al., 2016) 76.4 - Baseline: Our Method w/ 75.1 60.0 baseline relation detector Our Method 77.0 63.0 w/o entity re-ranking 74.9 60.6 w/o constraints - 58.0 Our Method (multi-detectors) 78.7 63.9 Table 3: KBQA results on SimpleQuestions (SQ) and WebQSP (WQ) test sets. The numbers in green color are directly comparable to our results since we start with the same entity linking results. Appendix C gives the detailed performance of the re-ranking step. (2) In contrast to the conclusion in (Yih et al., 2015), constraint detection is crucial for our system 12 . This is probably because our joint performance on topic entity and core-chain detection is more accurate (77.5% top-1 accuracy), leaving a huge potential (77.5% vs. 58.0%) for the

---

question. The KBQA system in the ﬁgure performs two key tasks: (1) entity linking , which links n -grams in questions to KB entities, and (2) relation detection , which identiﬁes the KB relation(s) a question refers to. The main focus of this work is to improve the relation detection subtask and further explore how it can contribute to the KBQA system. Although general relation detection 1 methods are well stud- ied in the NLP community, such studies usually do not take the end task of KBQA into considera- tion. As a result, there is a signiﬁcant gap between general relation detection studies and KB-speciﬁc relation detection. First, in most general relation detection tasks, the number of target relations is limited, normally smaller than 100. In contrast, in KBQA even a small KB, like Freebase2M (Bor- des et al., 2015), contains more than 6,000 relation types. Second, relation detection for KBQA often becomes a zero-shot learning task, since some test instances may have unseen relations in the training data. For example, the SimpleQuestions (Bordes et al., 2015) data set has 14% of the golden test relations not observed in golden training tuples. Third, as shown in Figure 1(b), for some KBQA tasks like WebQuestions (Berant et al., 2013), we need to predict a chain of relations instead of a single relation. This increases the number of tar- get relation types and the sizes of candidate rela- tion pools, further increasing the difﬁculty of KB relation detection. Owing to these reasons, KB re- lation detection is signiﬁcantly more challenging compared to general relation detection tasks. This paper improves KB relation detection to cope with the problems mentioned above. First, in order to deal with the unseen relations, we propose to break the relation names into word sequences for question-relation matching. Second,

---

given q as s rel ( r ; q ) = cos ( h r , h q ) . Intuitively, the proposed method should beneﬁt from hierarchical training since the second layer is ﬁtting the residues from the ﬁrst layer of matching, so the two layers of representations are more likely to be complementary to each other. This also en- sures the vector spaces of two layers are compara- ble and makes the second-layer training easier. During training we adopt a ranking loss to max- imizing the margin between the gold relation r + and other relations r − in the candidate pool R . l rel = max { 0 , γ − s rel ( r + ; q ) + s rel ( r − ; q ) } where γ is a constant parameter. Fig 2 sum- marizes the above Hierarchical Residual BiLSTM ( HR-BiLSTM ) model. Remark: Another way of hierarchical matching consists in relying on attention mechanism , e.g. (Parikh et al., 2016), to ﬁnd the correspondence between different levels of representations. This performs below the HR-BiLSTM (see Table 2). Detection This section describes our KBQA pipeline system. We make minimal efforts beyond the training of the relation detection model, making the whole system easy to build. Following previous work (Yih et al., 2015; Xu et al., 2016), our KBQA system takes an existing entity linker to produce the top- K linked entities, EL K ( q ) , for a question q (“ initial entity linking ”). Then we generate the KB queries for q following the four steps illustrated in Algorithm 1. Algorithm 1: KBQA with two-step relation detection top- K entity candidates EL K ( q ) Output: Top query tuple (ˆ e, ˆ r, { ( c, r c
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Relation detection as key component + 'hierarchical matching ... residual learning' contribution present.

## CEC-16

**Question:** Which 7 Indian languages do they experiment with?

**Reference answer(s):** Hindi, English, Kannada, Telugu, Assamese, Bengali and Malayalam ‖ Kannada, Hindi, Telugu, Malayalam, Bengali,  English and Assamese (in table, missing in text)

<details><summary>Gold evidence</summary>

> In this section, we describe our dataset collection process. We collected and curated around 635Hrs of audio data for 7 Indian languages, namely Kannada, Hindi, Telugu, Malayalam, Bengali, and English. We collected the data from the All India Radio news channel where an actor will be reading news for about 5-10 mins. To cover many speakers for the dataset, we crawled data from 2010 to 2019. Since the audio is very long to train any deep neural network directly, we segment the audio clips into smaller chunks using Voice activity detector. Since the audio clips will have music embedded during the news, we use Inhouse music detection model to remove the music segments from the dataset to make the dataset clean and our dataset contains 635Hrs of clean audio which is divided into 520Hrs of training data containing 165K utterances and 115Hrs of testing data containing 35K utterances. The amount of audio data for training and testing for each of the language is shown in the table bellow.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
the language is shown in the table bellow. Language Training (hrs) Testing (hrs) Hindi 113.08 19.65 English 55.86 19.19 Kannada 104.47 18.94 Telugu 110.01 11.62 Assamese 32.92 14.29 Bengali 63.59 20.62 Malayalam 37.82 10.88 Table 1 : Dataset In this section, we describe the feature extraction process and network architecture in detail. We use spectral features of 256 dimensions computed using 512 point FFT for every frame, and we add an energy feature for every frame giving us total 257 features for every frame. We use a window size of 25ms and frame shift of 10ms during feature computation. We crop random 5sec audio data from each utterance during training 2 https://github.com/wiseman/py-webrtcvad which results in a spectrogram of size 257x500 (features x number of features). We use these spectrograms as input to our CNN model during training. During testing, we compute the prediction score irrespective of the audio length. For the network architecture, we use ResNet-34 architec- ture, as described in [9]. The model uses convolution layers with Relu activations to map the spectrogram of size 257x500 input into 3D feature map of size 1x32x512. This feature cube is converted into 2D feature map of dimension 32x512 and fed into Ghost-VLAD/NetVLAD layer to generate a repre- sentation that has more language discrimination capacity. We use Adam optimizer with an initial learning rate of 0.01 and a ﬁnal learning rate of 0.00001 for training. Each model is trained for 15 epochs with early stopping criteria. For the baseline, we train an i-vector model using GMM- UBM. We ﬁt a small classiﬁer on top of the generated i- vectors to measure the accuracy. This model is referred as i-vector+svm . To compare our model with the previous state of the art system, we set up the x-vector language identi- ﬁcation system [8].

---

this work, we use Ghost-VLAD pooling approach that was originally proposed for face recognition to improve language identiﬁcation performance for Indian languages. We collected and curated 630 hrs audio data from news All India Radio news channel for 7 Indian languages. Our experimental re- sults shows that our approach outperforms the previous state of the art methods by an absolute 1.88% F1-score. We have also conducted experiments with different pooling strategies proposed in the past, and the GhostVLAD pooling approach turns out to be the best approach for aggregating frame-level features into a single utterance level feature. Our experiments also prove that our approach works much better even if the input during training contains smaller durations. Finally, we see that the embeddings generated by our method has very good language discriminative features and helps to improve the performance of language identiﬁcation. [1] N. Dehak, P. Kenny, R. Dehak, P. Dumouchel, and P. Ouellet, “Front-end factor analysis for speaker veriﬁ- cation,” IEEE Transactions on Audio, Speech,and Lan- guage Processing vol. 19, no. 4, pp. 788798, 2011. [2] P., Zhang, L., Ng, T., Glembek, O., Ma, J., Zhang, B., Mallidi, S.H. (2014) “Neural Network Bottleneck Fea- tures for Language Identiﬁcation,” Proc. Odyssey 2014 299-304. [3] I. Lopez-Moreno, J. Gonzalez-Dominguez, O. Plchot, D. Martinez, J. Gonzalez-Rodriguez, and P. Moreno, “Automatic language identiﬁcation using deep neural networks,” in Acoustics, Speech and Signal Process- ing (ICASSP), 2014 IEEE International Conference on. IEEE, 2014, pp. 53375341. [4] J. Gonzalez-Dominguez, I. Lopez-Moreno, H. Sak, J. Gonzalez-Rodriguez, and P. Moreno, “Automatic lan- guage identiﬁcation using long short-term memory re- current neural networks,”in Fifteenth Annual Conference of the International Speech Communication Association, 2014. [5] Lozano-Diez Alicia, Zazo-Candil, Ruben Gonzalez- Dominguez, Javier Toledano, Doroteo T. Gonzalez- Rodriguez, Joaquin “An end-to-end approach to language identiﬁcation in short utterances using convolutional neu-

---

IDENTIFICATION OF INDIAN LANGUAGES USING GHOST-VLAD POOLING Krishna D N, Ankita Patil, M.S.P Raj,Sai Prasad H S, Prabhu Aashish Garapati Youplus India, Bangalore { krishna, raj,ankita,saiprasad,aashish } @youplus.com In this work, we propose a new pooling strategy for language identiﬁcation by considering Indian languages. The idea is to obtain utterance level features for any variable length audio for robust language recognition. We use the GhostVLAD ap- proach to generate an utterance level feature vector for any variable length input audio by aggregating the local frame level features across time. The generated feature vector is shown to have very good language discriminative features and helps in getting state of the art results for language identiﬁ- cation task. We conduct our experiments on 635Hrs of au- dio data for 7 Indian languages. Our method outperforms the previous state of the art x-vector [11] method by an absolute improvement of 1.88% in F1-score and achieves 98.43% F1- score on the held-out test data. We compare our system with various pooling approaches and show that GhostVLAD is the best pooling approach for this task. We also provide visu- alization of the utterance level embeddings generated using Ghost-VLAD pooling and show that this method creates em- beddings which has very good language discriminative fea- tures. Pooling methods. The idea of language identiﬁcation is to classify a given audio signal into a particular class using a classiﬁcation al- gorithm. Commonly language identiﬁcation task was done using i-vector systems [1]. A very well known approach for language identiﬁcation proposed by N. Dahek et al. [1] uses the GMM-UBM model to obtain utterance level features called i-vectors. Recent advances in deep learning [15,16] have helped to improve the language identiﬁcation task us- ing many different neural network architectures which can be trained efﬁciently using GPUs for large scale

---

et al. [10], we use Ghost-VLAD to improve the accuracy of language identiﬁcation task for Indian languages. We explore multiple pooling strategies including NetVLAD pooling [11], Average pooling and Statistics pooling( as proposed in X- vectors [7]) and show that Ghost-VLAD pooling is the best pooling strategy for language identiﬁcation. Our model ob- tains the best accuracy of 98.24%, and it outperforms all the other previously proposed pooling methods. We conduct all our experiments on 635hrs of audio data for 7 Indian lan- guages collected from All India Radio news channel 1 . The paper is organized as follows. In section 2, we explain the proposed pooling method for language identiﬁcation. In sec- tion 3, we explain our dataset. In section 4, we describe the experiments, and in section 5, we describe the results. 1 http://www.newsonair.com/ arXiv:2002.01664v1 [cs.CL] 5 Feb 2020 In any language identiﬁcation model, we want to obtain utter- ance level representation which has very good language dis- criminative features. These representations should be com- pact and should be easily separable by a linear classiﬁer. The idea of any pooling strategy is to pool the frame-level rep- resentations into a single utterance level representation. Pre- vious works by [7] have used simple mean and standard de- viation aggregation to pool the frame-level features from the top layer of the neural network to obtain the utterance level features. Recently [9] used VLAD based pooling strategy for speaker identiﬁcation which is inspired from [10] pro- posed for face recognition. The NetVLAD [11] and Ghost- VLAD [10] methods are proposed for Place recognition and face recognition, respectively, and in both cases, they try to aggregate the local descriptors into global features. In our case, the local descriptors are features extracted from ResNet [15], and the global utterance level feature is obtained
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Table 1 lists all 7 languages.

## CEC-17

**Question:** Why are statistics from finite corpora unreliable?

**Reference answer(s):** $\mathit {PMI}(w,c)$ goes to negative infinity when the word-context pair $(w,c)$ does not appear in the training corpus ‖ A finite corpora may entirely omit rare word combinations

<details><summary>Gold evidence</summary>

> Unfortunately, $\mathit {PMI}(w,c)$ goes to negative infinity when the word-context pair $(w,c)$ does not appear in the training corpus. Due to unreliable statistics, this happens very frequently in finite corpora. Many models work around this issue by clipping negative $\mathit {PMI}$ values at 0, a measure known as Positive $\mathit {PMI}$ ($\mathit {PPMI}$), which works very well in practice. An unanswered question is: “What is lost/gained by collapsing the negative $\mathit {PMI}$ spectrum to 0?”. Understanding which type of information is captured by $\mathit {\texttt {-}PMI}$ can help in tailoring models for optimal performance.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Dense word vectors (or embeddings) are a key
component in modern NLP architectures for tasks
such as sentiment analysis, parsing, and machine
translation.
These vectors can be learned by
exploiting the distributional hypothesis ( Harris ,
1954 ), paraphrased by Firth ( 1957 ) as “a word is
characterized by the company that it keeps” , usu-
ally by constructing a cooccurrence matrix over
a training corpus, re-weighting it using Pointwise
Mutual Information ( PMI ) ( Church and Hanks ,
1990 ), and performing a low-rank factorization to
obtain dense vectors.
Unfortunately, PMI ( w, c ) goes to negative in-
ﬁnity when the word-context pair ( w, c ) does not
appear in the training corpus. Due to unreliable
statistics, this happens very frequently in ﬁnite
corpora.
Many models work around this issue
by clipping negative PMI values at 0 , a measure
known as Positive PMI ( PPMI ), which works
very well in practice.
An unanswered question
is: “What is lost/gained by collapsing the nega-
tive PMI spectrum to 0 ?” . Understanding which
type of information is captured by - PMI can help
in tailoring models for optimal performance.
In this work, we attempt to answer this ques-
tion by studying the kind of information contained
in the negative and positive spectrums of PMI
( - PMI and + PMI ). We evaluate weighted fac-
torization of different matrices which use either
- PMI , + PMI , or both on various semantic and
syntactic tasks. Results show that + PMI alone
performs quite well on most tasks, capturing both
semantics and syntax, in contrast to - PMI , which
performs poorly on nearly all tasks, except those
that test for syntax. Our main contribution is deep-
ening our understanding of distributional seman-
tics by extending Firth ( 1957 )’s paraphrase of the
distributional hypothesis to “a word is not only
characterized by the company that it keeps, but
also by the company it rejects” . Our secondary
contributions are the proposal of two PMI vari-
ants that account for the spectrum of - PMI , and
the justiﬁcation of the popular PPMI measure.

---

In distributional semantics, the pointwise mu-
tual information ( PMI ) weighting of the cooc-
currence matrix performs far better than raw
counts.
There is, however, an issue with
unobserved pair cooccurrences as PMI goes
to negative inﬁnity.
This problem is aggra-
vated by unreliable statistics from ﬁnite cor-
pora which lead to a large number of such
pairs. A common practice is to clip negative
PMI ( - PMI ) at 0 , also known as Positive
PMI ( PPMI ). In this paper, we investigate
alternative ways of dealing with - PMI and,
more importantly, study the role that negative
information plays in the performance of a low-
rank, weighted factorization of different PMI
matrices. Using various semantic and syntac-
tic tasks as probes into models which use ei-
ther negative or positive PMI (or both), we
ﬁnd that most of the encoded semantics and
syntax come from positive PMI , in contrast
to - PMI which contributes almost exclusively
syntactic information.
Our ﬁndings deepen
our understanding of distributional semantics,
while also introducing novel PMI variants
and grounding the popular PPMI measure.

---

many categories test for POS relations and are therefore syn-
tactic in nature.
4 Using https://github.com/zalandoresearch/ﬂair
Model
Semantic
Syntactic
SimLex
RW
GSem
STSB
WC
GSyn
POS
Dep
TopC
+ PPMI
.377
.352
56.1
.622
74.1
50.3
92.2
30.5
34.6
- CPMI - 2
.164
.231
3.6
.402
22.7
7.1
89.6
32.7
34.7
- NNEGPMI
.142
.232
3.3
.366
16.6
6.3
88.8
32.4
34.1
PPMI
.363
.459
80.3
.618
69.6
62.2
92.5
29.0
30.5
CPMI - 2
.355
.432
80.3
.621
69.9
65.1
92.6
28.5
31.1
NPMI
.322
.437
63.5
.578
58.0
58.0
92.1
29.2
31.4
NNEGPMI
.360
.439
80.7
.629
70.0
64.2
92.6
27.2
30.3
Random
-.018
-.026
0.0
.453
0.3
0.0
55.2
17.9
5.0
Table 1: SimLex and RW word similarity: Spearman rank correlation. STSB: Pearson correlation. GSem/GSyn
word analogy, POS tagging and WC, Dep, TopC probing tasks: % accuracy. Best result for each column in bold,
second best underlined.
Negative PMI: We observe that using only
- PMI (rows - CPMI - 2 and - NNEGPMI ) per-
forms similarly to all other models in POS tag-
ging and both syntactic probing tasks, but very
poorly on all semantic tasks, strongly supporting
our main claim that - PMI mostly encodes syn-
tactic information.
Our hypothesis for this is that the grammar
that generates language implicitly creates negative
cooccurrence and so - PMI encodes this syntac-
tic information. Interestingly, this idea creates a
bridge between distributional semantics and the
argument by Regier and Gahl ( 2004 ) that indirect
negative evidence might play an important role in
human language acquisition of grammar.
Positive PMI: The + PPMI model performs
as well or better as the full spectrum models on
nearly all tasks, clearly indicating that + PMI en-
codes both semantic and syntactic information.
Why incorporate -PMI? + PPMI only falters
on the RW and analogy tasks, and we hypothe-
size this is where - PMI is useful: in the absence
of positive information, negative information can
be used to improve rare word representations and
word analogies. Analogies are solved using near-
est neighbor lookups in the vector space, and so
accounting for negative cooccurrence effectively
repels words with which no positive cooccurrence
was observed. In future work, we will explore in-
corporating - PMI only for rare words (where it is
most needed).
Full spectrum models: The PPMI , CPMI - 2 ,
and
NNEGPMI
models
perform
similarly,
whereas the NPMI model is signiﬁcantly worst
on nearly all semantic tasks. We thus conclude
that accounting for scale in the positive spectrum
is more important than in the negative spectrum.
We hypothesize this is because scale helps to
uniquely identify words, which is critical for
semantics (results on WC task correlate strongly
with performance on semantic tasks), but in
syntax, words with the same function should be
indistinguishable.
Since + PMI encodes both
semantics and syntax, scale must be preserved,
whereas - PMI encodes mostly syntax, and so
scale information can be discarded.
Collapsing the negative spectrum:
The
PPMI model, which collapses the negative spec-
trum to zero, performs almost identically to the
CPMI - 2 and NNEGPMI models that account for
the range of negative values. This is justiﬁed by
1) Our discussion which shows that + PMI is far
more informative than - PMI and 2) Looking at
ﬁg. 1 , we see that collapsed values — interval
( − 5 , 0] — account for only 11% of samples com-
pared to 41 . 7% for non-collapsed negative values.
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Gold passage present verbatim (PMI -> -inf for unseen pairs).

## CEC-18

**Question:** What evaluation metrics are looked at for classification tasks?

**Reference answer(s):** Precision | Recall | F-measure | accuracy ‖ Precision, Recall and F-measure

<details><summary>Gold evidence</summary>

> Precision, Recall and F-measure for this multi-label classification are computed using a strategy similar to the one described in BIBREF21 . Let INLINEFORM0 be the set of predicted labels and INLINEFORM1 be the set of actual labels for the INLINEFORM2 instance. Precision and recall for this instance are computed as follows: INLINEFORM3
> We randomly selected 2000 sentences from the supervisor assessment corpus and manually tagged them (dataset D1). This labelled dataset contained 705, 103, 822 and 370 sentences having the class labels STRENGTH, WEAKNESS, SUGGESTION or OTHER respectively. We trained several multi-class classifiers on this dataset. Table TABREF10 shows the results of 5-fold cross-validation experiments on dataset D1. For the first 5 classifiers, we used their implementation from the SciKit Learn library in Python (scikit-learn.org). The features used for these classifiers were simply the sentence words along with their frequencies. For the last 2 classifiers (in Table TABREF10 ), we used our own implementation. The overall accuracy for a classifier is defined as INLINEFORM0 , where the denominator is 2000 for dataset D1. Note that the pattern-based approach is unsupervised i.e., it did not use any training data. Hence, the results shown for it are for the entire dataset and not based on cross-validation.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
within the HR community [13], [22], [10], [20]. The PA process in any modern organization is nowadays implemented and tracked through an IT system (the PA system ) that records the interactions that happen in various steps. Availability of this data in a computer-readable database opens up opportunities to analyze it using automated statistical, data- mining and text-mining techniques, to generate novel and actionable insights / patterns and to help in improving the quality and eﬀectiveness of the PA pro- cess [15], [19], [1]. Automated analysis of large-scale PA data is now facilitated 2 by technological and algorithmic advances, and is becoming essential for large organizations containing thousands of geographically distributed employees han- dling a wide variety of roles and tasks. A typical PA process involves purposeful multi-step multi-modal communica- tion between employees, their supervisors and their peers. In most PA processes, the communication includes the following steps: (i) in self-appraisal , an employee records his/her achievements, activities, tasks handled etc.; (ii) in supervisor as- sessment , the supervisor provides the criticism, evaluation and suggestions for improvement of performance etc.; and (iii) in peer feedback (aka 360 ◦ view ), the peers of the employee provide their feedback. There are several business ques- tions that managers are interested in. Examples: and suggestions of improvements found in the supervisor assessments? 2. For my workforce, how many supervisor comments are present for each of a given ﬁxed set of perspectives (which we call attributes ), such as FUNC- TIONAL EXCELLENCE , CUSTOMER FOCUS , BUILDING EFFECTIVE TEAMS etc.? 3. What is the summary of the peer feedback for a given employee? In this paper, we develop text mining techniques that can automatically produce answers to these questions. Since the intended users are HR executives, ideally, the techniques should work with minimum training

---

suggestions for im- provements found in the supervisor assessments and then used clustering to discover broad categories among them. As this is non-topical classiﬁcation, we found that SVM with ADWS kernel [16] produced the best results. We also used multi-class multi-label classiﬁcation techniques to match supervisor assessments to predeﬁned broad perspectives on performance. Logistic Regression classiﬁer was observed to produce the best results for this topical classiﬁcation. Finally, we proposed an ILP-based summarization technique to produce a summary of peer feedback comments for a given employee and compared it with manual summaries. The PA process also generates much structured data, such as supervisor ratings. It is an interesting problem to compare and combine the insights from discovered from structured data and unstructured text. Also, we are planning to automatically discover any additional performance attributes to the list of 15 attributes currently used by HR. 1. M. Apte, S. Pawar, S. Patil, S. Baskaran, A. Shrivastava, and G.K. Palshikar. Short text matching in performance management. In Proceedings of the 21st International 13 Conference on Management of Data (COMAD 2016) , pages 13–23, 2016. 2. Vitor R. Carvalho and William W. Cohen. Improving ”email speech acts” anal- ysis via n-gram selection. In Proceedings of the HLT-NAACL 2006 Workshop on Analyzing Conversations in Text and Speech , ACTS ’09, pages 35–41, 2006. 3. W.W. Cohen, V.R. Carvalho, and T.M. Mitchell. Learning to classify email into ”speech acts”. In Proc. Empirical Methods in Natural Language Processing (EMNLP-2004) , pages 309–316, 2004. 4. Rachel Cotterill. Question classiﬁcation for email. In Proc. Ninth Int. Conf. Com- putational Semantics (IWCS 2011) , 2011. 5. S. Deshpande, G.K. Palshilkar, and G Athiappan. An unsupervised approach to sentence classiﬁcation. In Proc. Int. Conf. on Management of Data (COMAD 2010) , pages 88–99, 2010. 6. Shantanu Godbole and Sunita Sarawagi.

---

Methods in Natural Language Processing (EMNLP- 2011) , 2011. 18. N. Ramrakhiyani, S. Pawar, and G.K. Palshikar. A system for classiﬁcation of propositions of the indian supreme court judgements. In Proc. 5th 2013 Forum on Information Retrieval Evaluation (FIRE 2013) , pages 1–4, 2013. 14 19. N. Ramrakhiyani, S. Pawar, G.K. Palshikar, and M. Apte. Aspects from appraisals: A label propagation with prior induction approach. In Proceedings of the 21st Inter- national Conference on Applications of Natural Language to Information Systems (NLDB 2016) , volume LNCS 9612, pages 301–309, 2016. 20. M. Schraeder, J. Becton, and R. Portis. A critical examination of performance appraisals. The Journal for Quality and Participation , (spring):20–25, 2007. 21. Andreas Stolcke, Klaus Ries, Noah Coccaro, Elizabeth Shriberg, Rebecca Bates, Daniel Jurafsky, Paul Taylor, Rachel Martin, Carol Van Ess-Dykema, and Marie Meteer. Dialogue act modeling for automatic tagging and recognition of conversa- tional speech. Computational Linguistics , 26(3), 2000. 22. C. Viswesvaran. Assessment of individual job performance: a review of the past century and a look ahead. In N. Anderson, D.S. Ones, H.K. Sinangil, and C. Viswes- varan, editors, Handbook of Industrial, Work and Organizational Psychology . Sage Publishers, 2001. 23. Y. Yamamoto and T. Takagi. A sentence classiﬁcation system for multi biomedical literature summarization. In Proc. 21st International Conference on Data Engi- neering Workshops , pages 1163–1168, 2005.

---

arXiv:1712.00991v1 [cs.CL] 4 Dec 2017 Mining Supervisor Evaluation and Peer Feedback in Performance Appraisals Girish Keshav Palshikar, Sachin Pawar, Saheb Chourasia, Nitin Ramrakhiyani TCS Research, Tata Consultancy Services Limited, 54B Hadapsar Industrial Estate, Pune 411013, India. { gk.palshikar, sachin7.p, saheb.c, nitin.ramrakhiyani } @tcs.com Abstract. Performance appraisal (PA) is an important HR process to periodically measure and evaluate every employee’s performance vis-a- vis the goals established by the organization. A PA process involves pur- poseful multi-step multi-modal communication between employees, their supervisors and their peers, such as self-appraisal, supervisor assessment and peer feedback. Analysis of the structured data and text produced in PA is crucial for measuring the quality of appraisals and tracking actual improvements. In this paper, we apply text mining techniques to produce insights from PA text. First, we perform sentence classiﬁca- tion to identify strengths, weaknesses and suggestions of improvements found in the supervisor assessments and then use clustering to discover broad categories among them. Next we use multi-class multi-label classi- ﬁcation techniques to match supervisor assessments to predeﬁned broad perspectives on performance. Finally, we propose a short-text summa- rization technique to produce a summary of peer feedback comments for a given employee and compare it with manual summaries. All tech- niques are illustrated using a real-life dataset of supervisor assessment and peer feedback text produced during the PA of 4528 employees in a large multi-national IT company. Performance appraisal (PA) is an important HR process, particularly for modern organizations that crucially depend on the skills and expertise of their workforce. The PA process enables an organization to periodically measure and evaluate every employee’s performance. It also provides a mechanism to link the goals established by the organization to its each employee’s day-to-day activities and performance. Design and analysis of PA processes is a lively area of research
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Intro/refs/abstract only; no evaluation metrics.

## CEC-19

**Question:** How many labels do the datasets have?

**Reference answer(s):** 719313 ‖ Book, Electronics, Beauty and Music each have 6000, IMDB 84919, Yelp 231163, Cell Phone 194792 and Baby 160792 labeled data.

<details><summary>Gold evidence</summary>

> Large-scale datasets: We further conduct experiments on four much larger datasets: IMDB (I), Yelp2014 (Y), Cell Phone (C), and Baby (B). IMDB and Yelp2014 were previously used in BIBREF25 , BIBREF26 . Cell phone and Baby are from the large-scale Amazon dataset BIBREF24 , BIBREF27 . Detailed statistics are summarized in Table TABREF9 . We keep all reviews in the original datasets and consider a transductive setting where all target examples are used for both training (without label information) and evaluation. We perform sampling to balance the classes of labeled source data in each minibatch INLINEFORM3 during training.
> Small-scale datasets: Our new dataset was derived from the large-scale Amazon datasets released by McAuley et al. ( BIBREF24 ). It contains four domains: Book (BK), Electronics (E), Beauty (BT), and Music (M). Each domain contains two datasets. Set 1 contains 6000 instances with exactly balanced class labels, and set 2 contains 6000 instances that are randomly sampled from the large dataset, preserving the original label distribution, which we believe better reflects the label distribution in real life. The examples in these two sets do not overlap. Detailed statistics of the generated datasets are given in Table TABREF9 .

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
nal vector representation ξ of the input document. Existing benchmark datasets such as the Amazon benchmark ( Blitzer et al. , 2007 ) typically remove reviews with neutral labels in both domains. This is problematic as the label information of the tar- get domain is not accessible in an unsupervised domain adaptation setting. Furthermore, remov- ing neutral instances may bias the dataset favor- ably for max-margin-based algorithms like ours, since the resulting dataset has all uncertain labels removed, leaving only high conﬁdence examples. Therefore, we construct new datasets by ourselves. The results on the original Amazon benchmark is qualitatively similar, and we present them in Ap- pendix A for completeness since most of previous works reported results on it. Small-scale datasets: Our new dataset was de- rived from the large-scale Amazon datasets 2 re- leased by McAuley et al. ( 2015 ). It contains four domains 3 : Book (BK), Electronics (E), Beauty (BT), and Music (M). Each domain contains two datasets. Set 1 contains 6000 instances with ex- actly balanced class labels, and set 2 contains 6000 instances that are randomly sampled from the large dataset, preserving the original label dis- tribution, which we believe better reﬂects the label distribution in real life. The examples in these two sets do not overlap. Detailed statistics of the gen- erated datasets are given in Table 1a . In all our experiments on the small-scale datasets, we use set 1 of the source domain as the only source with sentiment label information dur- ing training, and we evaluate the trained model on set 1 of the target domain. Since we cannot con- trol the label distribution of unlabeled data during training, we consider two different settings: Setting (1): Only set 1 of the target domain is used as the unlabeled set. This

---

(b) Large-scale datasets Table 1 : Summary of datasets. We have left the feature encoder G unspeciﬁed, for which, a few options can be considered. In our implementation, we adopt a one-layer CNN structure from previous works ( Kim , 2014 ; Yu and Jiang , 2016 ), as it has been demonstrated to work well for sentiment classiﬁcation tasks. Given a re- view document x = ( x 1 , x 2 , ..., x n ) consisting of n words, we begin by associating each word with a continuous word embedding ( Mikolov et al. , 2013 ) e x from an embedding matrix E ∈ R V × d , where V is the vocabulary size and d is the embed- ding dimension. E is jointly updated with other network parameters during training. Given a win- dow of dense word embeddings e x 1 , e x 2 , ..., e x l , the convolution layer ﬁrst concatenates these vec- tors to form a vector ˆx of length ld and then the output vector is computed by Equation ( 7 ): Conv ( ˆx ) = f ( W · ˆx + b ) (7) θ g = { W , b } is the parameter set of the en- coder G and is shared across all windows of the sequence. f is an element-wise non-linear activa- tion function. The convolution operation can cap- ture local contextual dependencies of the input se- quence and the extracted feature vectors are sim- ilar to n -grams. After the convolution operation is applied to the whole sequence, we obtain a list of hidden vectors H = ( h 1 , h 2 , ..., h n ) . A max- over-time pooling layer is applied to obtain the ﬁ-

---

tells us how the method performs in a condition when the target domain has a close-to-balanced label distribution. As we also evaluate on set 1 of the target domain, this is also considered as a transductive setting. Setting (2): Set 2 from both the source and target domains are used as unlabeled sets. Since set 2 is directly sampled from millions of reviews, it better reﬂects real-life sentiment distribution. Large-scale datasets: We further conduct ex- periments on four much larger datasets: IMDB 4 2 http://jmcauley.ucsd.edu/data/amazon/ 3 The original reviews were rated on a 5-point scale. We label them with rating < 3 , > 3 , and = 3 as negative, posi- tive, and neutral respectively. with rating < 5 , > 6 , and = 5 / 6 as negative, positive, and neutral respectively. (I), Yelp2014 (Y), Cell Phone (C), and Baby (B). IMDB and Yelp2014 were previously used in ( Tang et al. , 2015 ; Yang et al. , 2017 ). Cell phone and Baby are from the large-scale Amazon dataset ( McAuley et al. , 2015 ; He and McAuley , 2016 ). Detailed statistics are summarized in Ta- ble 1b . We keep all reviews in the original datasets and consider a transductive setting where all target examples are used for both training (without la- bel information) and evaluation. We perform sam- pling to balance the classes of labeled source data in each minibatch B ( s ) during training. Ideally, the development set should be drawn from the same distribution as the test set. However, un- der the unsupervised domain adaptation setting, we do not have any labeled target data at training phase which could be used as development set. In all of our experiments, for each pair of domains, we instead sample 1000

---

( t ) i is estimated as the predicted label distribution ˜ y ( t ) i , which is a function of θ g and θ f . The loss can thus be written as Γ = − 1 n t n t X i =1 C X j =1 ˜ y ( t ) i ( j ) log ˜ y ( t ) i ( j ) (5) Assume the domain discrepancy can be effectively reduced through feature adaptation, by minimiz- ing the entropy penalty, training of the classiﬁer is inﬂuenced by the unlabeled target data and will generally maximize the margins between the tar- get examples and the decision boundaries, increas- ing the prediction conﬁdence on the target domain. Self-ensemble Bootstrapping: Another way to estimate y ( t ) i corresponds to bootstrapping. The idea is to estimate the unknown labels as the predictions of the model learned from the pre- vious round of training. Bootstrapping has been explored for domain adaptation in previous works ( Jiang and Zhai , 2007 ; Wu et al. , 2009 ). However, in their methods, domain discrepancy was not explicitly minimized via feature adap- tation. Applying bootstrapping or other semi- supervised learning techniques in this case may worsen the results as the classiﬁer can perform quite bad on the target data. Inspired by the ensembling method proposed in ( Laine and Aila , 2017 ), we estimate y ( t ) i by forming ensemble predictions of labels during training, using the outputs on different training epochs. The loss is formulated as follows: Ω= − 1 N N X i =1 C X j =1 ˜ z ( s,t ) i ( j ) log ˜ y ( s,t ) i ( j ) (6) where ˜ z denotes
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Small-scale 6000-instance sets present, but large-scale label counts (IMDB, Yelp, etc.) missing.

## CEC-20

**Question:** What is the state-of-the-art model for the task?

**Reference answer(s):** OpATT BIBREF6 | Neural Content Planning with conditional copy (NCP+CC) BIBREF4

<details><summary>Gold evidence</summary>

> Table TABREF23 displays the automatic evaluation results on both development and test set. We chose Conditional Copy (CC) model as our baseline, which is the best model in Wiseman. We included reported scores with updated IE model by Puduppully and our implementation's result on CC in this paper. Also, we compared our models with other existing works on this dataset including OpATT BIBREF6 and Neural Content Planning with conditional copy (NCP+CC) BIBREF4. In addition, we implemented three other hierarchical encoders that encoded tables' row dimension information in both record-level and row-level to compare with the hierarchical structure of encoder in our model. The decoder was equipped with dual attention BIBREF9. The one with LSTM cell is similar to the one in N18-2097 with 1 layer from {1,2,3}. The one with CNN cell BIBREF10 has kernel width 3 from {3, 5} and 10 layer from {5,10,15,20}. The one with transformer-style encoder (MHSA) BIBREF11 has 8 head from {8, 10} and 5 layer from {2,3,4,5,6}. The heads and layers mentioned above were for both record-level encoder and row-level encoder respectively. The self-attention (SA) cell we used, as described in Section SECREF3, achieved better overall performance in terms of F1% of CS, CO and BLEU among the hierarchical encoders. Also we implemented a template system same as the one used in Wiseman which outputted eight sentences: an introductory sentence (two teams' points and who win), six top players' statistics (ranked by their points) and a conclusion sentence. We refer the readers to Wiseman's paper for more detailed information on templates. The gold reference's result is also included in Table TABREF23. Overall, our model performs better than other neural models on both development and test set in terms of RG's P%, F1% score of CS, CO and BLEU, indicating our model's clear improvement on generating high-fidelity, informative and fluent texts. Also, our model with three dimension representations outperforms hierarchical encoders with only row dimension representation on development set. This indicates that cell and time dimension representation are important in representing the tables. Compared to reported baseline result in Wiseman, we achieved improvement of $22.27\%$ in terms of RG, $26.84\%$ in terms of CS F1%, $35.28\%$ in terms of CO and $18.75\%$ in terms of BLEU on test set. Unsurprisingly, template system achieves best on RG P% and CS R% due to the included domain knowledge. Also, the high RG # and low CS P% indicates that template will include vast information while many of them are deemed redundant. In addition, the low CO and low BLEU indicates that the rigid structure of the template will produce texts that aren't as adaptive to the given tables and natural as those produced by neural models. Also, we conducted ablation study on our model to evaluate each component's contribution on development set. Based on the results, the absence of row-level encoder hurts our model's performance across all metrics especially the content selection ability.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
... the rigid structure of the template will pro- duce texts that aren’t as adaptive to the given tables and natural as those produced by neural models. Also, we conducted ablation study on our model to evaluate each component’s contribution on de- velopment set. Based on the results, the absence of row-level encoder hurts our model’s performance across all metrics especially the content selection ability. Row, column and time dimension information are important to the modeling of tables because subtracting any of them will result in performance Model RG CS CO BLEU P% # P% R% DLD% Gold 96.0117.17100.00100.00100.00 100.00 TEM 99.9754.14 23.88 72.63 11.90 8.33 CC 75.2616.3732.63 39.62 15.34 14.03 DEL ∗ 84.8619.3130.81 38.79 16.34 16.19 NCP 87.9924.5035.97 55.85 16.98 16.22 Ours 92.5122.73 38.52 52.98 19.95 16.69 Table 2: Automatic evaluation results on test set. Re- sults were obtained using Wiseman et al. ( 2017 )’s trained extractive evaluation models with relexicaliza- tion ( Li and Wan , 2018 ). ∗ We include delayed copy (DEL)’s result in the paper ( Li and Wan , 2018 ) for com- parison. drop. Also, position embedding is critical when modeling time dimension information according to the results. In addition, record fusion gate plays
an important role because BLEU, CO, RG P%
and CS P% drop signiﬁcantly after subtracting it
from full model. Results show that each compo-
nent in the model contributes to the overall perfor-
mance. In addition, we compare our model with
delayed copy model (DEL) ( Li and Wan , 2018 )
along with gold text, template system (TEM), con-
ditional copy (CC) ( Wiseman et al. , 2017 ) and
NCP+CC (NCP) ( Puduppully et al. , 2019 ). Li and
Wan ( 2018 )’s model generate a template at ﬁrst
and then ﬁll in the slots with delayed copy mech-
anism. Since its result in Li and Wan ( 2018 )’s pa-
per was evaluated by IE model trained by Wise-
man et al. ( 2017 ) and “relexicalization” by Li and
Wan ( 2018 ), we adopted the corresponding IE
model and re-implement “relexicalization” as sug- gested by Li and Wan ( 2018 ) for fair comparison. Please note that CC’s evaluation results via our re- implemented “relexicalization” is comparable to the reported result in Li and Wan ( 2018 ). We ap- plied them on models other than DEL as shown in Table 2 and report DEL’s result from ( Li and Wan , 2018 )’s paper. It shows that our model outperform Li and Wan ( 2018 )’s model signiﬁcantly across all automatic evaluation metrics in Table 2 .

---

... to learn the represen- tation of the table cell. Speciﬁcally, we employ three self-attention models to obtain three repre- sentations of the table cell in its row, column and time dimension. Then, in the second layer, we design a record fusion gate to identify the more important representation from those three dimen- sion and combine them into a dense vector. In the third layer, we use mean pooling method to merge the previously obtained table cell representations in the same row into the representation of the ta- ble’s row. Then, we use self-attention with content selection gate ( Puduppully et al. , 2019 ) to ﬁlter unimportant rows’ information. To the best of our knowledge, this is the ﬁrst work on neural table- to-text generation via modeling column and time dimension information so far. We conducted ex- periments on ROTOWIRE. Results show that our model outperforms existing systems, improving baseline BLEU from 14.19 to 16.85 ( +18 . 75% ), P% of relation generation (RG) from 74.80 to 91.46 ( +22 . 27% ), F1% of content selection (CS) from 32.49 to 41.21 ( +26 . 84% ) and content order- ing (CO) from 15.42 to 20.86 ( +35 . 28% ) on test
set. It also exceeds the state-of-the-art model in
terms of those metrics.

---

In recent years, neural data-to-text systems make
remarkable progress on generating texts directly
from data. Mei et al. ( 2016 ) proposes an encoder-
aligner-decoder model to generate weather fore-
cast, while Jain et al. ( 2018 ) propose a mixed
hierarchical attention.
Sha et al. ( 2018 ) pro-
poses a hybrid content- and linkage-based atten-
tion mechanism to model the order of content. Liu
et al. ( 2018 ) propose to integrate ﬁeld informa-
tion into table representation and enhance decoder
with dual attention. Bao et al. ( 2018 ) develops
a table-aware encoder-decoder model. Wiseman
et al. ( 2017 ) introduced a document-scale data-to-
text dataset, consisting of long text with more re-
dundant records, which requires the model to se-
lect important information to generate.
We de-
scribe recent works in Section 1 .
Also, some
studies in abstractive text summarization encode
long texts in a hierarchical manner. Cohan et al.
( 2018 ) uses a hierarchical encoder to encode in-
put, paired with a discourse-aware decoder. Ling
and Rush ( 2017 ) encode document hierarchically
and propose coarse-to-ﬁne attention for decoder.
Recently, Liu et al. ( 2019 ) propose a hierarchi-
cal encoder for data-to-text generation which uses
LSTM as its cell. Murakami et al. ( 2017 ) propose
to model stock market time-series data and gen-
erate comments. As for incorporating historical
background in generation, Robin ( 1994 ) proposed
to build a draft with essential new facts at ﬁrst,
then incorporate background facts when revising
the draft based on functional uniﬁcation gram-
mars. Different from that, we encode the historical
(time dimension) information in the neural data-
to-text model in an end-to-end fashion. Existing
works on data-to-text generation neglect the joint
representation of tables’ row, column and time di-
mension information. In this paper, we propose an
effective hierarchical encoder which models infor-
mation from row, column and time dimension si-
multaneously.
```
</details>

- **Judgment:** `[ ] YES   [X] NO   [ ] UNSURE`
- **Note (optional):** DEFERRED (Claude unsure): compares against CC, DEL, NCP+CC and says it 'exceeds the state-of-the-art model', but never says which one is SOTA; NCP is the strongest baseline in Table 2. OpATT absent. Leaning NO.

## CEC-21

**Question:** What is the recent abstractive summarization method in this paper?

**Reference answer(s):** pointer networks with coverage mechanism (PG-net) ‖  pointer networks with coverage mechanism (PG-net)BIBREF0

<details><summary>Gold evidence</summary>

> To overcome the size issue of the student reflection dataset, we first explore the effect of incorporating domain transfer into a recent abstractive summarization model: pointer networks with coverage mechanism (PG-net)BIBREF0. To experiment with domain transfer, the model was pretrained using the CNN/DM dataset, then fine tuned using the student reflection dataset (see the Experiments section). A second approach we explore to overcome the lack of reflection data is data synthesis. We first propose a template model for synthesizing new data, then investigate the performance impact of using this data when training the summarization model. The proposed model makes use of the nature of datasets such as ours, where the reference summaries tend to be close in structure: humans try to find the major points that students raise, then present the points in a way that marks their relative importance (recall the CS example in Table TABREF4). Our third explored approach is to combine domain transfer with data synthesis.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Abstractive
Summarization .
Abstractive
summariza-
tion aims to generate coherent summaries with high
readability, and has seen increasing interest and im-
proved performance due to the emergence of seq2seq
models
(Sutskever, Vinyals, and Le 2014)
and
atten-
tion
mechanisms
(Bahdanau, Cho, and Bengio 2014).
For
example,
(See, Liu, and Manning 2017),
(Paulus, Xiong, and Socher 2018),
and
(Gehrmann, Deng, and Rush 2018)
in
addition
to
us-
ing encoder-decoder model with attention, they used
pointer networks to solve the out of vocabulary is-
sue, while (See, Liu, and Manning 2017) used coverage
mechanism to solve the problem of word repetition.
In
addition,
(Paulus, Xiong, and Socher 2018)
and
(Chen and Bansal 2018)
used
reinforcement
learning
in an end-to-end setting.
To our knowledge, training such neural abstractive sum-
marization models in low resource domains using domain
transfer has not been thoroughly explored on domains dif-
ferent than news. For example, (Nallapati et al. 2016) re-
ported the results of training on CNN/DM data while eval-
uating on DUC data without any tuning. Note that these
two datasets are both in the news domain, and both consist
of well written, structured documents. The domain transfer
experiments of (Gehrmann, Deng, and Rush 2018) similarly
used two different news summarization datasets (CNN/DM
and NYT). Our work differs in several ways from these two
prior domain transfer efforts. First, our experiments involve
two entirely different domains: news and student reﬂections.
Unlike news, student reﬂection documents lack global struc-

---

Recently, with the emergence of neural seq2seq models,
abstractive
summarization
methods
have
seen
great
performance
strides
(See, Liu, and Manning 2017;
Gehrmann, Deng, and Rush 2018;
Paulus, Xiong, and Socher 2018).
However,
complex
neural summarization models with thousands of pa-
rameters
usually
require
a
large
amount
of
train-
ing data. In fact, much of the neural summarization
work has been trained and tested in news domains
where
numerous
large
datasets
exist.
For
example,
the
CNN/DailyMail
(CNN/DM)
(Hermann et al. 2015;
Nallapati et al. 2016) and New York Times (NYT) datasets
are in the magnitude of 300k and 700k documents,
respectively. In contrast, in other domains such as stu-
dent
reﬂections,
summarization datasets
are
only
in
the magnitude of tens or hundreds of documents (e.g.,
(Luo and Litman 2015)).
We
hypothesize that
training
Copyright c ⃝ 2019, Association for the Advancement of Artiﬁcial
Intelligence (www.aaai.org). All rights reserved.
complex neural abstractive summarization models in such
domains will not yield good performing models, and we will
indeed later show that this is the case for student reﬂections.
To
improve
performance
in
low
resource
do-
mains,
we
explore
three
directions.
First,
we
ex-
plore
domain
transfer
for
abstractive
summariza-
tion.
While
domain
transfer
is
not
new,
compared
to
prior
summarization
studies
(Hua and Wang 2017;
Keneshloo, Ramakrishnan, and Reddy 2019), our training
(news) and tuning (student reﬂection) domains are quite dis-
similar, and the in-domain data is small. Second, we propose
a template-based synthesis method to create synthesized
summaries, then explore the effect of enriching training data
for abstractive summarization using the proposed model
compared to a synthesis baseline. Lastly, we combine both
directions. Evaluations of neural abstractive summarization
method across four student reﬂection corpora show the
utility of all three methods.

---

arXiv:2002.03407v1  [cs.CL]  9 Feb 2020
Abstractive Summarization for Low Resource Data using Domain Transfer and
Data Synthesis
Ahmed Magooda 1 , Diane Litman 1

---

Training abstractive summarization models typically requires
large amounts of data, which can be a limitation for many
domains. In this paper we explore using domain transfer and
data synthesis to improve the performance of recent abstrac-
tive summarization methods when applied to small corpora of
student reﬂections. First, we explored whether tuning state of
the art model trained on newspaper data could boost perfor-
mance on student reﬂection data. Evaluations demonstrated
that summaries produced by the tuned model achieved higher
ROUGE scores compared to model trained on just student re-
ﬂection data or just newspaper data. The tuned model also
achieved higher scores compared to extractive summariza-
tion baselines, and additionally was judged to produce more
coherent and readable summaries in human evaluations. Sec-
ond, we explored whether synthesizing summaries of student
data could additionally boost performance. We proposed a
template-based model to synthesize new data, which when
incorporated into training further increased ROUGE scores.
Finally, we showed that combining data synthesis with do-
main transfer achieved higher ROUGE scores compared to
only using one of the two approaches.

---

used two different news summarization datasets (CNN/DM
and NYT). Our work differs in several ways from these two
prior domain transfer efforts. First, our experiments involve
two entirely different domains: news and student reﬂections.
Unlike news, student reﬂection documents lack global struc-
ture, are repetitive, and contain many sentence fragments
and grammatical mistakes. Second, the prior approaches ei-
ther trained a part of the model using NYT data while re-
taining the other part of the model trained only on CNN/DM
data (Gehrmann, Deng, and Rush 2018), or didn’t perform
any tuning at all (Nallapati et al. 2016). In contrast, we do
the training in two consecutive phases, pretraining and ﬁne
tuning. Finally, (Gehrmann, Deng, and Rush 2018) reported
that while training with domain transfer outperformed train-
ing only on out-of-domain data, it was not able to beat train-
ing only on in-domain data. This is likely because their in
and out-of-domain data sizes are comparable, unlike in our
case of scarce in-domain data.
In a different approach to abstractive summarization,
(Cao et al. 2018) developed a soft template based neural
method consisting of an end-to-end deep model for template
retrieval, reranking and summary rewriting. While we also
develop a template based model, our work differs in both
model structure and purpose.
Data Synthesis . Data synthesis for text summariza-
tion is underexplored, with most prior work focus-
ing
on
machine
translation,
and
text
normalization.
(Zhang, Zhao, and LeCun 2015)
proposed
doing
data
```
</details>

- **Judgment:** `[ ] YES   [X] NO   [ ] UNSURE`
- **Note (optional):** DEFERRED (Claude unsure): context discusses See et al. pointer networks + coverage, but never says that's the model this paper uses. Leaning NO.

## CEC-22

**Question:** What are method's improvements of F1 for NER task for English and Chinese datasets?

**Reference answer(s):** English datasets including CoNLL2003 and OntoNotes5.0, our proposed method outperforms BERT-MRCBIBREF38 by +0.29 and +0.96 respectively | Chinese datasets, achieving F1 improvements by +0.97 and +2.36 on MSRA and OntoNotes4.0, respectively ‖ For English datasets including CoNLL2003 and OntoNotes5.0, our proposed method outperforms BERT-MRCBIBREF38 by +0.29 and +0.96 respectively. | huge performance boosts on Chinese datasets, achieving F1 improvements by +0.97 and +2.36 on MSRA and OntoNotes4.0, respectively

<details><summary>Gold evidence</summary>

> For the NER task, we consider both Chinese datasets, i.e., OntoNotes4.0 BIBREF34 and MSRA BIBREF35, and English datasets, i.e., CoNLL2003 BIBREF36 and OntoNotes5.0 BIBREF37.
> Table shows experimental results on NER datasets. For English datasets including CoNLL2003 and OntoNotes5.0, our proposed method outperforms BERT-MRCBIBREF38 by +0.29 and +0.96 respectively. We observe huge performance boosts on Chinese datasets, achieving F1 improvements by +0.97 and +2.36 on MSRA and OntoNotes4.0, respectively. As far as we are concerned, we are setting new SOTA performances on all of the four NER datasets.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Settings
Named entity recognition (NER) is the
task of detecting the span and semantic category of
entities within a chunk of text. Our implementation
uses the current state-of-the-art model proposed by
Li et al. ( 2019 ) as the backbone, and changes the
MLE loss to DSC loss. Datasets that we use in-
clude OntoNotes4.0 ( Pradhan et al. , 2011 ), MSRA
( Levow , 2006 ), CoNLL2003 ( Sang and Meulder ,
2003 ) and OntoNotes5.0 ( Pradhan et al. , 2013 ). We
report span-level micro-averaged precision, recall
and F1.
Baselines
We use the following baselines:
• ELMo: a tagging model with pretraining
from Peters et al. ( 2018 ).
• Lattice-LSTM: Zhang and Yang ( 2018 ) con-
structs a word-character lattice, only used in
Chinese datasets.
• CVT: Clark et al. ( 2018 ) uses Cross-View
Training(CVT) to improve the representations
of a Bi-LSTM encoder.
• Bert-Tagger: Devlin et al. ( 2018 ) treats NER
as a tagging task.
• Glyce-BERT: Wu et al. ( 2019 ) combines Chi-
nese glyph information with BERT pretrain-
ing.
• BERT-MRC:
Li et al. ( 2019 ) formulates
NER as a machine reading comprehension
task and achieves SOTA results on Chinese
English CoNLL 2003
Model
Prec.
Rec.
F1
ELMo( Peters et al. , 2018 )
-
-
92.22
CVT( Clark et al. , 2018 )
-
-
92.6
BERT-Tagger( Devlin et al. , 2018 )
-
-
92.8
BERT-MRC( Li et al. , 2019 )
92.33 94.61
93.04
BERT-MRC+FL
93.13 93.09
93.11
(+0.06)
BERT-MRC+DL
93.22 93.12
93.17
(+0.12)
BERT-MRC+DSC
93.41 93.25
93.33
(+0.29)
English OntoNotes 5.0
Model
Prec.
Rec.
F1
CVT ( Clark et al. , 2018 )
-
-
88.8
BERT-Tagger ( Devlin et al. , 2018 )
90.01 88.35
89.16

---

1440–1448.
Ross B. Girshick, Jeff Donahue, Trevor Darrell, and
Jitendra Malik. 2013.
Rich feature hierarchies for
accurate object detection and semantic segmentation.
2014 IEEE Conference on Computer Vision and Pattern
Recognition , pages 580–587.
Fr ´ ederic Godin. 2019. Improving and Interpreting Neu-
ral Networks for Word-Level Prediction Tasks in Natural
Language Processing . Ph.D. thesis, Ghent University,
Belgium.
Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian
Sun. 2015. Deep residual learning for image recogni-
tion. 2016 IEEE Conference on Computer Vision and
Pattern Recognition (CVPR) , pages 770–778.
Lu Jiang, Zhengyuan Zhou, Thomas Leung, Li-Jia Li,
and Li Fei-Fei. 2017. Mentornet: Learning data-driven
curriculum for very deep neural networks on corrupted
labels. In ICML .
H. Kahn and A. W. Marshall. 1953. Methods of reduc-
ing sample size in monte carlo computations. Opera-
tions Research , 1(5):263–278.
Anil
Kanduri,
Mohammad
Hashem
Haghbayan,
Amir M. Rahmani, Muhammad Shafique, Axel Jantsch,
and Pasi Liljeberg. 2018.
adboost: Thermal aware
performance boosting through dark silicon patterning.
IEEE Trans. Computers , 67(8):1062–1077.
Angelos Katharopoulos and Fran c¸ ois Fleuret. 2018. Not
all samples are created equal: Deep learning with im-
portance sampling. In ICML .
Tom ´ a ˇ s Ko ˇ cisk ` y, Jonathan Schwarz, Phil Blunsom, Chris
Dyer, Karl Moritz Hermann, G ´ aabor Melis, and Edward
Grefenstette. 2018. The narrativeqa reading compre-
hension challenge. Transactions of the Association of
Computational Linguistics , 6:317–328.

---

Table 3 presents the experimental results
on Chinese datasets. As can be seen, the proposed
DSC loss outperforms the best baseline results by
a large margin, i.e., outperforming BERT-tagger
by +1.86 in terms of F1 score on CTB5, +1.80 on
CTB6 and +2.19 on UD1.4. As far as we know,
we are achieving SOTA performances on the three
datasets. Focal loss only obtains a little perfor-
mance improvement on CTB5 and CTB6, and the
dice loss obtains huge gain on CTB5 but not on
CTB6, which indicates the three losses are not con-
sistently robust in solving the data imbalance issue.
Table 4 presents the experimental results for En-
glish datasets.

---

tagging.
A.2
Named Entity Recognition
Datasets
For the NER task, we consider both
Chinese datasets, i.e., OntoNotes4.0 5 and MSRA 6
, and English datasets, i.e., CoNLL2003 7 and
OntoNotes5.0 8 .
• CoNLL2003 is an English dataset with 4 en-
tity types: Location, Organization, Person and
Miscellaneous. We followed data processing
protocols in ( Ma and Hovy , 2016 ).
• English OntoNotes5.0 consists of texts from
a wide variety of sources and contains 18 en-
tity types. We use the standard train/dev/test
split of CoNLL2012 shared task.
• Chinese MSRA performs as a Chinese bench-
mark dataset containing 3 entity types. Data in
MSRA is collected from news domain. Since
the development set is not provided in the
original MSRA dataset, we randomly split
2 https://catalog.ldc.upenn.edu/
LDC2005T01
3 https://catalog.ldc.upenn.edu/
LDC2007T36
4 https://universaldependencies.org/
5 https://catalog.ldc.upenn.edu/
LDC2011T03
6 http://sighan.cs.uchicago.edu/
bakeoff2006/
7 https://www.clips.uantwerpen.be/
conll2003/ner/
8 https://catalog.ldc.upenn.edu/
LDC2013T19
the training set into training and development
splits by 9:1. We use the official test set for
evaluation.
• Chinese OntoNotes4.0 is a Chinese dataset
and consists of texts from news domain, which
has 18 entity types. In this paper, we take the
same data split as Wu et al. ( 2019 ) did.
A.3
Machine Reading Comprephension
Datasets
For MRC task, we use three datasets:
SQuADv1.1/v2.0 9 and Queref 10 datasets.
• SQuAD v1.1 and SQuAD v2.0 are the most
widely used QA benchmarks.
SQuAD1.1
is a collection
of 100K crowdsourced

---

98.91
(+0.05)
BERT-Tagger+DSC
99.41 98.93
99.38
(+0.52)
English Tweets
Model
Prec.
Rec.
F1
FastText+CNN+CRF( Godin , 2019 )
-
-
91.78
BERT-Tagger ( Devlin et al. , 2018 )
92.33 91.98
92.34
BERT-Tagger+FL
91.24 93.22
92.47
(+0.13)
BERT-Tagger+DL
91.44 92.88
92.52
(+0.18)
BERT-Tagger+DSC
92.87 93.54
92.58
(+0.24)
Table 4: Experimental results for English POS datasets.
( Xue et al. , 2005 ) 5.0/6.0 and UD1.4 and English
datasets including Wall Street Journal (WSJ) and
the dataset proposed by Ritter et al. ( 2011 ). We re-
port the span-level micro-averaged precision, recall
and F1 for evaluation.
Baselines
We used the following baselines:
• Joint-POS: Shao et al. ( 2017 ) jointly learns
Chinese word segmentation and POS.
• Lattice-LSTM: Zhang and Yang ( 2018 ) con-
structs a word-character lattice network.
• Bert-Tagger: Devlin et al. ( 2018 ) treats part-
of-speech as a tagging task.
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Only English CoNLL2003 (+0.29) visible; OntoNotes5.0 and Chinese MSRA/OntoNotes4.0 gains missing.

## CEC-23

**Question:** What predictive model do they build?

**Reference answer(s):** logistic regression models ‖ logistic regression models based on unigram bag-of-words features (BOW), sentiment signals (SENT), the linguistic features from our earlier analyses (LING), and combinations of these features.

<details><summary>Gold evidence</summary>

> We compare the predictions of logistic regression models based on unigram bag-of-words features (BOW), sentiment signals (SENT), the linguistic features from our earlier analyses (LING), and combinations of these features. BOW and SENT provide baselines for the task. We compute BOW features using term frequency-inverse document frequency (TF-IDF) and category-based features by normalizing counts for each category by the number of words in each document. The BOW classifiers are trained with regularization (L2 penalties of 1.5).

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
We now show how we can use the linguistic feature
sets we have described to build a classiﬁer that pre-
dicts dogmatism in comments. A predictive model
further validates our feature sets, and also allows us
to analyze dogmatism in millions of other Reddit
comments in a scalable way, with multiple uses in
ongoing, downstream analyses.
Prediction task. Our goal is (1) to understand
how well we can use the strategies in Section 3
to predict dogmatism, and (2) to test the domain-
independence of these strategies. First, we test the
performance of our model under cross-validation
within the Reddit comment dataset. We then eval-
uate the Reddit-based model on a held out corpus
of New York Times comments annotated using the
technique in Section 2. We did not refer to this sec-
ond dataset during feature construction.
For classiﬁcation, we consider two classes of
comments: dogmatic and non-dogmatic . As in the
prior analysis, we draw these comments from the top
and bottom quartiles of the dogmatism distribution.
This means the classes are balanced, with 2,500 total
comments in the Reddit training data and 500 total
comments in the New York Times testing data.
We compare the predictions of logistic regression
models based on unigram bag-of-words features
(BOW), sentiment signals 2 (SENT), the linguistic
2 For SENT, we use normalized word counts from LIWC’s
positive and negative emotional categories.
features from our earlier analyses (LING), and com-
binations of these features. BOW and SENT provide
baselines for the task. We compute BOW features
using term frequency-inverse document frequency
(TF-IDF) and category-based features by normaliz-
ing counts for each category by the number of words
in each document. The BOW classiﬁers are trained
with regularization (L2 penalties of 1.5).
Classiﬁcation results. We present classiﬁcation
accuracy in Table 2. BOW shows an AUC of 0.853
within Reddit and 0.776 on the held out New York
Times comments. The linguistic features boost clas-
siﬁcation results within Reddit (0.881) and on the
held out New York Times comments (0.791). While
linguistic signals by themselves provide strong pre-
dictive power (0.801 AUC within domain), senti-
ment signals are much less predictive.
These results suggest that linguistic features in-
spired by prior efforts in psychology are useful
for predicting dogmatism in practice and generalize
across new domains.

---

We have constructed the ﬁrst corpus of social me-
dia posts annotated with dogmatism scores, allowing
us to explore linguistic features of dogmatism and
build a predictive model that analyzes new content.
We apply this model to Reddit, where we discover
behavioral predictors of dogmatism and topical pat-
terns in the comments of dogmatic users.
Could we use this computational model to help
users shed their dogmatic beliefs? Looking forward,
our work makes possible new avenues for encourag-
ing pro-social behavior in online communities.

---

dogmatism? (R3)
We have shown dogmatism is captured by many lin-
guistic features, but can we discover other high-level
user behaviors that are similarly predictive?
To ﬁnd out, we compute metrics of user behavior
using the data sample of 1000 users and 10 million
posts described in Section 5.2. Speciﬁcally, we cal-
culate (1) activity : a user’s total number of posts, (2)
breadth : the number of subreddits a user has posted
in, (3) focus : the proportion of a user’s posts that
appear in the subreddit where they are most active,
and (4) engagement : the average number of posts a
user contributes to each discussion they engage in.
We then ﬁt these behavioral features to a linear re-
gression model where we predict each user’s average
dogmatism level. Positive coefﬁcients in this model
are positively predictive of dogmatism, while nega-
tive coefﬁcients are negatively predictive.
We ﬁnd this model is signiﬁcantly predicitive of
dogmatism ( R 2 = 0 . 1 , p < 0 . 001 ), with all features
reaching statistical signiﬁcance ( p < 0 . 001 ). Activ-
ity and focus are positively associated with dogma-
tism, while breadth and engagement are negatively
associated (Table 5). Together, these results suggest
dogmatic users tend to post frequently and in spe-
ciﬁc communities, but are not as inclined to continue
to engage with a discussion, once it has begun.

---

“I’m supposed to trust the opinion of a MS min-
ion? The people that produced Windows ME, Vista
and 8? They don’t even understand people, yet they
think they can predict the behavior of new, self-
guiding AI?” – anonymous
“I think an AI would make it easier for Patients to
conﬁde their information because by nature, a robot
cannot judge them. Win-win? :D”’ – anonymous
Dogmatism describes the tendency to lay down
opinions as incontrovertibly true, without respect for
conﬂicting evidence or the opinions of others (Ox-
ford Dictionary, 2016). Which user is more dog-
matic in the examples above? This question is sim-
ple for humans. Phrases like “they think” and “they
don’t even understand,” suggest an intractability of
opinion, while “I think” and “win-win?” suggest
the opposite. Can we train computers to draw sim-
ilar distinctions?
Work in psychology has called
out many aspects of dogmatism that can be modeled
computationally via natural language, such as over-
conﬁdence and strong emotions (Rokeach, 1954).
We present a statistical model of dogmatism that
addresses two complementary goals. First, we val-
idate psychological theories by examining the pre-
dictive power of feature sets that guide the model’s
predictions. For example, do linguistic signals of
certainty help to predict a post is dogmatic, as the-
ory would suggest? Second, we apply our model to
answer four questions:
R1 : What kinds of topics (e.g., guns, LGBT) at-
tract the highest levels of dogmatism?
R2 : How do dogmatic beliefs cluster?
R3 : How does dogmatism inﬂuence a conversa-
tion on social media?
R4 : How do other user behaviors (e.g., frequency
and breadth of posts) relate to dogmatism?
We train a predictive model to classify dogmatic
posts from Reddit, one of the most popular discus-
sion communities on the web. 1 Posts on Reddit cap-
ture discussion and debate across a diverse set of do-
mains and topics – users talk about everything from
climate change and abortion, to world news and re-
lationship advice, to the future of artiﬁcial intelli-
gence. As a prerequisite to training our model, we
have created a corpus of 5,000 Reddit posts anno-
tated with levels of dogmatism, which we are releas-
ing to share with other researchers.
1 http://www.reddit.com
arXiv:1609.00425v1  [cs.CL]  1 Sep 2016
Figure 1: We crowdsourced dogmatism labels for 5000 com-
ments. The distribution is slightly skewed towards higher lev-
els of dogmatism. For example, crowdworkers unanimously la-
beled 206 comments as highly dogmatic ( 5 × 3 = 15 ), but only
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Gold passage present: logistic regression with BOW/SENT/LING features.

## CEC-24

**Question:** Which types of named entities do they recognize?

**Reference answer(s):** PER, LOC, ORG, MISC ‖ PER | LOC | ORG | MISC

<details><summary>Gold evidence</summary>

> The SnapCaptions dataset is composed of 10K user-generated image (snap) and textual caption pairs where named entities in captions are manually labeled by expert human annotators (entity types: PER, LOC, ORG, MISC). These captions are collected exclusively from snaps submitted to public and crowd-sourced stories (aka Snapchat Live Stories or Our Stories). Examples of such public crowd-sourced stories are “New York Story” or “Thanksgiving Story”, which comprise snaps that are aggregated for various public events, venues, etc. All snaps were posted between year 2016 and 2017, and do not contain raw images or other associated information (only textual captions and obfuscated visual descriptor features extracted from the pre-trained InceptionNet are available). We split the dataset into train (70%), validation (15%), and test sets (15%). The captions data have average length of 30.7 characters (5.81 words) with vocabulary size 15,733, where 6,612 are considered unknown tokens from Stanford GloVE embeddings BIBREF22 . Named entities annotated in the SnapCaptions dataset include many of new and emerging entities, and they are found in various surface forms (various nicknames, typos, etc.) To the best of our knowledge, SnapCaptions is the only dataset that contains natural image-caption pairs with expert-annotated named entities.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
and named entity recognition. In Proceedings of the Workshop on Noisy User-generated Text . William Chan, Navdeep Jaitly, Quoc V Le, and Oriol Vinyals. 2015. Listen, attend and spell. arXiv:1508.01211 . Jason PC Chiu and Eric Nichols. 2015. Named entity recognition with bidirectional lstm-cnns. arXiv:1511.08308 . Paramveer Dhillon, Dean P Foster, and Lyle H Ungar. 2011. Multi-view learning of word embeddings via cca. In NIPS . pages 199–207. John Duchi, Elad Hazan, and Yoram Singer. 2011. Adaptive subgradient methods for online learning and stochastic optimization. JMLR . Desmond Elliott, Stella Frank, and Eva Hasler. 2015. Multi-language image description with neural se- quence models. CoRR, abs/1510.04709 . Zhiheng Huang, Wei Xu, and Kai Yu. 2015. Bidi- rectional lstm-crf models for sequence tagging. arXiv:1508.01991 . John Lafferty, Andrew McCallum, and Fernando CN Pereira. 2001. Conditional random ﬁelds: Prob- abilistic models for segmenting and labeling se- quence data . Guillaume Lample, Miguel Ballesteros, Sandeep Sub- ramanian, Kazuya Kawakami, and Chris Dyer. 2016. Neural architectures for named entity recognition. NAACL . Xuezhe Ma and Eduard Hovy. 2016. End-to-end sequence labeling via bi-directional lstm-cnns-crf. arXiv preprint arXiv:1603.01354 . Andrew McCallum and Wei Li. 2003. Early results for named entity recognition with conditional random ﬁelds, feature induction and web-enhanced lexicons. In NAACL . Tomas Mikolov, Kai Chen, Greg Corrado, and Jeffrey Dean. 2013. Efﬁcient estimation of word represen- tations in vector space. ICLR . Seungwhan Moon and Jaime Carbonell. 2017. Com- pletely heterogeneous transfer learning with atten- tion: What and what not to transfer. IJCAI . Seungwhan Moon, Suyoun Kim, and Haohan Wang. 2015. Multimodal transfer deep learning with appli- cations in audio-visual recognition. In NIPS MMML Workshop . Alexandre Passos, Vineet Kumar, and Andrew McCal- lum. 2014. Lexicon infused phrase embeddings for named entity resolution. aarXiv:1404.5367 . Jeffrey Pennington, Richard Socher, and Christo- pher D.

---

Multimodal Named Entity Recognition for Short Social Media Posts Seungwhan Moon 1,2 , Leonardo Neves 2 , Vitor Carvalho 3 2 Snap Research 3 Intuit seungwhm@cs.cmu.edu, lneves@snap.com, vitor carvalho@intuit.com We introduce a new task called Multimodal Named Entity Recognition (MNER) for noisy user-generated data such as tweets or Snapchat captions, which comprise short text with ac- companying images. These social media posts often come in inconsistent or incomplete syn- tax and lexical notations with very limited surrounding textual contexts, bringing signif- icant challenges for NER. To this end, we cre- ate a new dataset for MNER called SnapCap- tions (Snapchat image-caption pairs submitted to public and crowd-sourced stories with fully annotated named entities). We then build upon the state-of-the-art Bi-LSTM word/character based NER models with 1) a deep image net- work which incorporates relevant visual con- text to augment textual information, and 2) a generic modality-attention module which learns to attenuate irrelevant modalities while amplifying the most informative ones to ex- tract contexts from, adaptive to each sam- ple and token. The proposed MNER model with modality attention signiﬁcantly outper- forms the state-of-the-art text-only NER mod- els by successfully leveraging provided visual contexts, opening up potential applications of MNER on myriads of social media platforms. Social media with abundant user-generated posts provide a rich platform for understanding events, opinions and preferences of groups and individ- uals. These insights are primarily hidden in un- structured forms of social media posts, such as in free-form text or images without tags. Named entity recognition (NER), the task of recognizing named entities from free-form text, is thus a criti- cal step for building structural information, allow- ing for its use in personalized assistance, recom- mendations, advertisement, etc. While many previous approaches ( Lample et al. , 2016 ; Ma and Hovy , 2016 ;

---

Chiu and (a) (b) Figure 1: Multimodal NER + modality attention . (a) Visual contexts help recognizing polysemous entity names (‘Monopoly’ as in a board game versus an eco- nomics term). (b) Modality attention successfully sup- presses word embeddings of a unknown token (‘Marsh- melloooo’ with erroneously trailing ‘o’s), and focuses on character-based context ( e.g. capitalized ﬁrst letter, and lexical similarity to a known named entity (‘Marsh- mello’, a music producer)) for correct prediction. Nichols , 2015 ; Huang et al. , 2015 ) on NER have shown success for well-formed text in recognizing named entities via word context resolution ( e.g. LSTM with word embeddings) combined with character-level features ( e.g. CharLSTM/CNN), several additional challenges remain for recog- nizing named entities from extremely short and coarse text found in social media posts. For in- stance, short social media posts often do not pro- vide enough textual contexts to resolve polyse- mous entities ( e.g. “monopoly is da best ”, where ‘monopoly’ may refer to a board game (named entity) or a term in economics). In ad- dition, noisy text includes a huge number of un- known tokens due to inconsistent lexical notations and frequent mentions of various newly trending entities ( e.g. “xoxo Marshmelloooo ”, where ‘Marshmelloooo’ is a mis-spelling of a known entity ‘Marshmello’, a music producer), making arXiv:1802.07862v1 [cs.CL] 22 Feb 2018 word embeddings based neural networks NER models vulnerable. To address the challenges above for social me- dia posts, we build upon the state-of-the-art neu- ral architecture for NER with the following two novel approaches (Figure 1 ). First, we propose to leverage auxiliary modalities for additional con- text resolution of entities. For example, many pop- ular social media platforms now provide ways to compose a post in multiple modalities - speciﬁ- cally image and

---

Manning. 2014. Glove: Global vectors for word representation. In EMNLP . Lev Ratinov and Dan Roth. 2009. Design challenges and misconceptions in named entity recognition. In CoNLL . Marek Rei, Gamal KO Crichton, and Sampo Pyysalo. 2016. Attending to characters in neural sequence labeling models. COLING . Olga Russakovsky, Jia Deng, Hao Su, Jonathan Krause, Sanjeev Satheesh, Sean Ma, Zhiheng Huang, An- drej Karpathy, Aditya Khosla, Michael Bernstein, Alexander C. Berg, and Li Fei-Fei. 2015. ImageNet Large Scale Visual Recognition Challenge. IJCV . Erik F Sang and Jorn Veenstra. 1999. Representing text chunks. In EACL . Lucia Specia, Stella Frank, Khalil Sima’an, and Desmond Elliott. 2016. A shared task on multi- modal machine translation and crosslingual image description. In WMT . Sainbayar Sukhbaatar, Jason Weston, Rob Fergus, et al. C. Szegedy, W. Liu, Y. Jia, P. Sermanet, S. E. Reed, D. Anguelov, D. Erhan, V. Vanhoucke, and A. Ra- binovich. 2014. Going deeper with convolutions. CVPR . Christian Szegedy, Vincent Vanhoucke, Sergey Ioffe, Jonathon Shlens, and Zbigniew Wojna. 2015. Re- thinking the inception architecture for computer vi- sion. CoRR . Oriol Vinyals, Alexander Toshev, Samy Bengio, and Dumitru Erhan. 2015. Show and tell: A neural im- age caption generator. In CVPR . Kelvin Xu, Jimmy Ba, Ryan Kiros, Kyunghyun Cho, Aaron Courville, Ruslan Salakhutdinov, Richard S Zemel, and Yoshua Bengio. 2015. Show, attend and tell: Neural image caption generation with visual at- tention. ICML . Li Yao, Atousa Torabi, Kyunghyun Cho, Nicolas Bal- las, Christopher Pal, Hugo Larochelle, and Aaron Courville. 2015. Describing videos by exploiting temporal structure. In ICCV .
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Abstract/intro/refs only; PER/LOC/ORG/MISC never mentioned.

## CEC-25

**Question:** What is the average length of the sentences?

**Reference answer(s):** 15.5 ‖ average:15.5

<details><summary>Gold evidence</summary>

> In this paper, we used the supervisor assessment and peer feedback text produced during the performance appraisal of 4528 employees in a large multi-national IT company. The corpus of supervisor assessment has 26972 sentences. The summary statistics about the number of words in a sentence is: min:4 max:217 average:15.5 STDEV:9.2 Q1:9 Q2:14 Q3:19.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
In this paper, we used the supervisor assessment and peer feedback text produced
during the performance appraisal of 4528 employees in a large multi-national IT
company. The corpus of supervisor assessment has 26972 sentences. The sum-
mary statistics about the number of words in a sentence is: min:4 max:217 av-
erage:15.5 STDEV:9.2 Q1:9 Q2:14 Q3:19.
4
Sentence Classiﬁcation
The PA corpus contains several classes of sentences that are of interest. In this
paper, we focus on three important classes of sentences viz., sentences that
discuss strengths (class STRENGTH ), weaknesses of employees (class WEAK-
NESS ) and suggestions for improving her performance (class SUGGESTION ).
The strengths or weaknesses are mostly about the performance in work carried
out, but sometimes they can be about the working style or other personal
4
qualities. The classes WEAKNESS and SUGGESTION are somewhat overlapping;
e.g., a suggestion may address a perceived weakness. Following are two example sentences in each class. STRENGTH : – Excellent technology leadership and delivery capabilities along with ability to groom technology champions within the team. – He can drive team to achieve results and can take pressure. WEAKNESS : – Sometimes exhibits the quality that he knows more than the others in the room which puts off others. – Tends to stretch himself and team a bit too hard. SUGGESTION : – X has to attune himself to the vision of the business unit and its goals a little more than what is being currently exhibited. – Need to improve on business development skills, articulation of business and solution benefits. Several linguistic aspects of these classes of sentences are apparent. The sub- ject is implicit in many sentences. The strengths are often mentioned as either noun phrases (NP) with positive adjectives ( Excellent technology leadership ) or positive nouns ( engineering strength ) or through verbs with positive po- larity ( dedicated ) or as verb phrases containing positive adjectives ( delivers innovative solutions ). Similarly for weaknesses, where negation is more fre- quently used ( presentations are not his forte ), or alternatively, the polarities of verbs ( avoid ...

---

1. M. Apte, S. Pawar, S. Patil, S. Baskaran, A. Shrivastava, and G.K. Palshikar. Short
text matching in performance management. In Proceedings of the 21st International
13
Conference on Management of Data (COMAD 2016) , pages 13–23, 2016.
2. Vitor R. Carvalho and William W. Cohen. Improving ”email speech acts” anal-
ysis via n-gram selection. In Proceedings of the HLT-NAACL 2006 Workshop on
Analyzing Conversations in Text and Speech , ACTS ’09, pages 35–41, 2006.
3. W.W. Cohen, V.R. Carvalho, and T.M. Mitchell.
Learning to classify email
into ”speech acts”. In Proc. Empirical Methods in Natural Language Processing
(EMNLP-2004) , pages 309–316, 2004.
4. Rachel Cotterill. Question classiﬁcation for email. In Proc. Ninth Int. Conf. Com-
putational Semantics (IWCS 2011) , 2011.
5. S. Deshpande, G.K. Palshilkar, and G Athiappan. An unsupervised approach to
sentence classiﬁcation.
In Proc. Int. Conf. on Management of Data (COMAD
2010) , pages 88–99, 2010. 6. Shantanu Godbole and Sunita Sarawagi. Discriminative methods for multi-labeled classiﬁcation. In PAKDD 2004 , pages 22–30, 2004. 7. B. Hachey and C. Grover. Sequence modelling for sentence classiﬁcation in a legal summarisation system. In Proc. 2005 ACM Symposium on Applied Computing , 2005. 8. George Karypis. Cluto-a clustering toolkit. Technical report, DTIC Document, 2002. 9. A. Khoo, Y. Marom, and D. Albrecht. Experiments with sentence classiﬁcation. In Proc. 2006 Australasian Language Technology Workshop (ALTW2006) , pages 18–25, 2006. 10. P.E. Levy and J.R. Williams. The social context of performance appraisal: a review and framework for the future. Journal of Management , 30(6):881–905, 2004. 11. Chin-Yew Lin. Rouge: A package for automatic evaluation of summaries. In Text summarization branches out: Proceedings of the ACL-04 workshop , volume 8. Barcelona, Spain, 2004. 12. L. McKnight and P. Srinivasan. Categorization of sentence types in medical ab- stracts. In Proc. American Medical Informatics Association Annual Symposium , pages 440–444, 2003. 13. K.R. Murphy and J. Cleveland. Understanding Performance Appraisal: Social, Organizational and Goal-Based Perspective . Sage Publishers, 1995. 14. Stanislaw Osinski, Jerzy Stefanowski, and Dawid Weiss. Lingo: Search results clus- tering algorithm based on singular value decomposition. In Intelligent Information Processing and Web ...

---

... 5 ≥ 1 C 6 : P N i =1 ( Innovation i · X i ) + S 6 ≥ 1 C 7 : P N i =1 ( Communication i · X i ) + S 7 ≥ 1 C 8 : P N i =1 ( Customer i · X i ) + S 8 ≥ 1 C 9 : P N i =1 ( Strategy i · X i ) + S 9 ≥ 1 C 10 : P N i =1 ( Personal i · X i ) + S 1 0 ≥ 1 (At least one phrase should be chosen to represent each leadership attribute) C 11 : P N i =1 P N j =1 ,s.t.i ̸ = j ( S ij · ( X i + X j − 1)) + S 11 < = 0 (No duplicate phrases should be chosen) C 12 : P N i =1 ( InvalidSingleNoun i · X i ) − S 12 < = 0 (Single word noun phrases are not preferred if they are not noun.attribute ) 12 algorithms is number of sentences keep in the ﬁnal summary. ILP-based summa- rization requires a similar parameter K, which is automatically decided based on
number of total candidate phrases. Assuming a sentence is equivalent to roughly
3 phrases, for Sumy algorithms, we set number of sentences parameter to the
ceiling of K/3. Table 9 shows average and standard deviation of ROUGE un-
igram f1 scores for each algorithm, over the 100 summaries. The performance
of ILP-based summarization is comparable with the other algorithms, as the
two sample t-test does not show statistically signiﬁcant diﬀerence. Also, human
evaluators preferred phrase-based summary generated by our approach to the
other sentence-based summaries.
Table 9. Comparative performance of various summarization algorithms
Algorithm
ROUGE unigram F1
Average
Std. Deviation
LSA
0.254
0.146
TextRank
0.254
0.146
LexRank
0.258
0.148
ILP-based summary
0.243
0.15
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) 'average:15.5' present verbatim.

## CEC-26

**Question:** what are the pivot-based baselines?

**Reference answer(s):** pivoting | pivoting$_{\rm m}$ ‖ firstly translates a source language into the pivot language which is later translated to the target language

<details><summary>Gold evidence</summary>

> Table TABREF19 and TABREF26 report zero-shot results on Europarl and Multi-UN evaluation sets, respectively. We compare our approaches with related approaches of pivoting, multilingual NMT (MNMT) BIBREF19, and cross-lingual transfer without pretraining BIBREF16. The results show that our approaches consistently outperform other approaches across languages and datasets, especially surpass pivoting, which is a strong baseline in the zero-shot scenario that multilingual NMT systems often fail to beat BIBREF19, BIBREF20, BIBREF23. Pivoting translates source to pivot then to target in two steps, causing inefficient translation process. Our approaches use one encoder-decoder model to translate between any zero-shot directions, which is more efficient than pivoting. Regarding the comparison between transfer approaches, our cross-lingual pretraining based transfer outperforms transfer method that does not use pretraining by a large margin.
> Although it is challenging for one model to translate all zero-shot directions between multiple distant language pairs of MultiUN, MLM+BRLM-SA still achieves better performances on Es $\rightarrow $ Ar and Es $\rightarrow $ Ru than strong pivoting$_{\rm m}$, which uses MNMT to translate source to pivot then to target in two separate steps with each step receiving supervised signal of parallel corpora. Our approaches surpass pivoting$_{\rm m}$ in all zero-shot directions by adding back translation BIBREF33 to generate pseudo parallel sentences for all zero-shot directions based on our pretrained models such as MLM+BRLM-SA, and further training our universal encoder-decoder model with these pseudo data. BIBREF22 gu2019improved introduces back translation into MNMT, while we adopt it in our transfer approaches. Finally, our best MLM+BRLM-SA with back translation outperforms pivoting$_{\rm m}$ by 2.4 BLEU points averagely, and outperforms MNMT BIBREF22 by 4.6 BLEU points averagely. Again, in supervised translation directions, MLM+BRLM-SA with back translation also achieves better performance than the original supervised Transformer.
> We use traditional transfer learning, pivot-based method and multilingual NMT as our baselines. For the fair comparison, the Transformer-big model with 1024 embedding/hidden units, 4096 feed-forward filter size, 6 layers and 8 heads per layer is adopted for all translation models in our experiments. We set the batch size to 2400 per batch and limit sentence length to 100 BPE tokens. We set the $\text{attn}\_\text{drop}=0$ (a dropout rate on each attention head), which is favorable to the zero-shot translation and has no effect on supervised translation directions BIBREF22. For the model initialization, we use Facebook's cross-lingual pretrained models released by XLM to initialize the encoder part, and the rest parameters are initialized with xavier uniform. We employ the Adam optimizer with $\text{lr}=0.0001$, $t_{\text{warm}\_\text{up}}=4000$ and $\text{dropout}=0.1$. At decoding time, we generate greedily with length penalty $\alpha =1.0$.
> Pivot-based Method is a common strategy to obtain a source$\rightarrow $target model by introducing a pivot language. This approach is further divided into pivoting and pivot-synthetic. While the former firstly translates a source language into the pivot language which is later translated to the target language BIBREF4, BIBREF5, BIBREF12, the latter trains a source$\rightarrow $target model with pseudo data generated from source-pivot or pivot-target parallel data BIBREF13, BIBREF14. Although the pivot-based methods can achieve not bad performance, it always falls into a computation-expensive and parameter-vast dilemma of quadratic growth in the number of source languages, and suffers from the error propagation problem BIBREF15.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
We compare our ap- proaches with related approaches of pivoting, multilingual NMT (MNMT) (Johnson et al. 2016), and cross-lingual transfer without pretraining (Kim, Gao, and Ney 2019). The results show that our approaches consistently outperform other approaches across languages and datasets, especially surpass pivoting, which is a strong baseline in the zero- shot scenario that multilingual NMT systems often fail to beat (Johnson et al. 2016; Al-Shedivat and Parikh 2019; Arivazhagan et al. 2018). Pivoting translates source to pivot then to target in two steps, causing inefﬁcient trans- lation process. Our approaches use one encoder-decoder model to translate between any zero-shot directions, which is more efﬁcient than pivoting. Regarding the comparison between transfer approaches, our cross-lingual pretraining based transfer outperforms transfer method that does not use pretraining by a large margin. Results on Europarl Dataset. Regarding comparison be- tween the baselines in table 2, we ﬁnd that pivoting is the strongest baseline that has signiﬁcant advantage over other two baselines. Cross-lingual transfer for languages without shared vocabularies (Kim, Gao, and Ney 2019) manifests the worst performance because of not using source ↔ pivot par- allel data, which is utilized as beneﬁcial supervised signal for the other two baselines. Our best approach of MLM+BRLM-SA achieves the sig- niﬁcant superior performance to all baselines in the zero- shot directions, improving by 0.9-4.8 BLEU points over the strong pivoting. Meanwhile, in the supervised direction of pivot → target, our approaches performs even better than the original supervised Transformer thanks to the shared en- MultiUN Ar,Es,Ru ↔ En Direction Ar → Es Es → Ar Ar → Ru Ru → Ar Es → Ru Ru → Es A-ZST A-ST Baselines Cross-lingual Transfer 10.26 12.44 4.58 4.42 13.80 7.93 8.90 44.73 MNMT(Johnson et al. 2016) 27.40 20.18 15.12 16.19 17.88 27.93 20.78 43.95 Pivoting m

---

Isahara, H. 2007. A comparison of pivot methods for phrase-based statistical machine translation. In HLT-NAACL . Vaswani, A.; Shazeer, N.; Parmar, N.; Uszkoreit, J.; Jones, L.; Gomez, A. N.; Kaiser, L.; and Polosukhin, I. 2017. At- tention is all you need. In NIPS . Wu, Y.; Schuster, M.; Chen, Z.; Le, Q. V.; Norouzi, M.; Macherey, W.; Krikun, M.; Cao, Y.; Gao, Q.; Macherey, K.; et al. 2016. Google’s neural machine translation system: Bridging the gap between human and machine translation. arXiv preprint arXiv:1609.08144 . Zheng, H.; Cheng, Y.; and Liu, Y. P. 2017. Maximum ex- pected likelihood estimation for zero-resource neural ma- chine translation. In IJCAI . Zhu, X.; He, Z.; Wu, H.; Wang, H.; Zhu, C.; and Zhao, T. 2013. Improving pivot-based statistical machine translation using random walk. In EMNLP . Zoph, B.; Yuret, D.; May, J.; and Knight, K. 2016. Trans- fer learning for low-resource neural machine translation. In EMNLP .

---

ofﬁcial validation and test sets. For vocabulary, we use 60K sub-word tokens based on Byte Pair Encoding (BPE) (Sennrich, Haddow, and Birch 2015). For MultiUN corpus, we use four languages: English (En) is set as the pivot language, which has parallel data Europarl Fr → En → Es De → En → Fr Ro → En → De Direction Fr → Es En → Es De → Fr En → Fr Ro → De En → De Baselines Cross-lingual Transfer (Kim, Gao, and Ney 2019) 18.45 34.01 9.86 34.05 2.02 23.61 MNMT(Johnson et al. 2016) 27.12 34.69 21.36 33.87 9.31 24.09 MNMT Agreement (Al-Shedivat and Parikh 2019) 29.91 33.80 24.45 32.55 - - Pivoting 32.25 34.01 27.79 34.05 14.74 23.61 Proposed Cross-lingual Pretraining Based Transfer MLM 35.96 34.83 27.61 35.66 12.64 22.04 MLM+TLM 36.78 34.73 29.45 35.33 14.39 24.96 MLM+BRLM-HA 36.30 34.98 29.91 34.99 14.21 24.26 MLM+BRLM-SA 37.02 34.92 30.66 35.91 15.62 24.95 Table 2: Results on Europarl test sets. Three pivot settings are conducted in our experiments. In each setting, the left column presents the zero-shot performances (source → target), and the right column denotes the performances in the supervised parent model direction (pivot → target). with other three languages which do not have parallel data between each other. The three languages are Arabic (Ar), Spanish (Es), and Russian (Ru), and mutual translation be- tween themselves constitutes six zero-shot translation di- rection for evaluation. We use 80K BPE splits as the vo- cabulary. Note that all sentences are tokenized by the tok- enize.perl 2 script, and we lowercase all data to avoid a large vocabulary for the MultiUN corpus. Experimental Details. We use traditional transfer learn- ing, pivot-based method and multilingual NMT as our base- lines. For the fair comparison, the Transformer-big model with 1024 embedding/hidden units, 4096 feed-forward

---

(BRLM) is designed to make full use of the source ↔ pivot bilingual data to obtain a universal encoder for different languages. Once the universal encoder is con- structed, we only need to train the pivot → target model and then test this model in source → target direction directly. The main contributions of this paper are as follows: • We propose a new transfer learning approach for NMT which uses the cross-lingual language model pre-training to enable a high performance on zero-shot translation. • We propose a novel pre-training method called BRLM, which can effectively alleviates the distance between dif- ferent source language spaces. • Our proposed approach signiﬁcantly improves zero-shot translation performance, consistently surpassing pivot- ing and multilingual approaches. Meanwhile, the perfor- mance on supervised translation direction remains the same level or even better when using our method. In recent years, zero-shot translation in NMT has attracted widespread attention in academic research. Existing meth- ods are mainly divided into four categories: pivot-based method, transfer learning, multilingual NMT, and unsuper- vised NMT. • Pivot-based Method is a common strategy to obtain a source → target model by introducing a pivot language. This approach is further divided into pivoting and pivot- synthetic. While the former ﬁrstly translates a source lan- guage into the pivot language which is later translated to the target language (Kauers et al. 2002; de Gispert and Mariño 2006; Utiyama and Isahara 2007), the lat- ter trains a source → target model with pseudo data gener- ated from source-pivot or pivot-target parallel data (Chen et al. 2017; Zheng, Cheng, and Liu 2017). Although the pivot-based methods can achieve not bad performance, it always falls into a computation-expensive and parameter- vast dilemma of quadratic growth in the number of source languages, and suffers from the error propagation prob-
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Pivot-based method definition and Pivoting in Europarl table present.

## CEC-27

**Question:** what datasets did they use?

**Reference answer(s):** Dataset of total 3500 questions from the Internet and other sources such as books of general knowledge questions, history, etc. ‖ 3500 questions collected from the internet and books.

<details><summary>Gold evidence</summary>

> Though Bengali is the seventh most spoken language in terms of number of native speakers BIBREF23, there is no standard corpus of questions available BIBREF0. We have collected total 3500 questions from the Internet and other sources such as books of general knowledge questions, history etc. The corpus contains the questions and the classes each question belongs to.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
A. Popular Question-Answering Systems
Over the years, a handful of QA systems have gained
popularity around the world. One of the oldest QA system is
BASEBALL (created on 1961) [15] which answers question
related to baseball league in America for a particular season.
LUNAR [25] system answers questions about soil samples
taken from Apollo lunar exploration. Some of the most popular
QA Systems are IBM Watson, Apple Siri and Wolfram Alpha.
Examples of some QA systems based on different languages
are: Zhang Yu Chinese question classiﬁcation [26] based on
Incremental Modiﬁed Bayes, Arabic QA system (AQAS) [18]
by F. A. Mohammed, K. Nasser, & H. M. Harb and Syntactic
open domain Arabic QA system for factoid questions [7] by
Fareed et al. QA systems have been built on different analysis
methods such as morphological analysis [12], syntactical anal-
ysis [29], semantic analysis [24] and expected answer Type
analysis [4].
B. Research Works Related to Question Classiﬁcations
Researches on question classiﬁcation, question taxonomies
and QA system have been undertaken in recent years. There
are two types of approaches for question classiﬁcation ac-
cording to Banerjee et al in [1] - by rules and by machine
learning approach. Rule based approaches use some hard
coded grammar rules to map the question to an appropriate
answer type [21] [23]. Machine Learning based approaches
have been used by Zhang et al and Md. Aminul Islam et al in
[28] and [14]. Many classiﬁers have been used in machine
learning for QC such as Support Vector Machine (SVM)
[28] [19], Support Vector Machines and Maximum Entropy
Model [13], Naive Bayes (NB), Kernel Naive Bayes (KNB),
Decision Tree (DT) and Rule Induction (RI) [1]. In [14], they
claimed to achieve average precision of 0.95562 for coarse
class and 0.87646 for ﬁner class using Stochastic Gradient
Descent (SGD).
arXiv:1911.03059v2  [cs.CL]  19 Nov 2019
C. Research Works in Bengali Language
A Bengali QC System was built by Somnath Banerjee
and Sivaji Bandyopadhyay [1] [2] [3]. They proposed a two-
layer taxonomy classiﬁcation with 9 coarse-grained classes
and 69 ﬁne-grained classes. There are other research works
[14] [16] in Bengali Language. A survey was performed on
text QA techniques [8] where there was an analysis conducted
in Bengali Language. Syed Mehedi Hasan Nirob et al achieved
88.62% accuracy by using 380 top frequent words as the
feature in their work [19].

---

system. In the ﬁrst setup, we eliminate the stop words from
the text using another dataset containing only stop words. At
second step, we work without eliminating the stop words from
the text which gives better result than the ﬁrst setup.
B. Classiﬁcation Algorithms

---

By implementing different machine learning based classi-
ﬁers on our Bengali question corpus, we perform a compara-
tive analysis among them. The question classiﬁcation impacts
the QA system. So, it is important to classify the question
more precisely. This work will help the research community
to choose a proper classiﬁcation model for smart Bengali QA
system development. Future work should aim at developing a
richer corpus of Bengali questions which will help in getting
better vector representation of words and thus will facilitate
deep learning based automatic feature extraction.

---

... pages 445–448, 2016. [15] Bert F Green Jr. Baseball: an automatic question-answerer. In Papers presented at the May 9-11, 1961, western joint IRE-AIEE-ACM computer conference , pages 219–224, 1961. [16] Fasihul kabir. Bengali text document categorization using stochastic gradient descent (sgd) classiﬁer. In 2015 International Conference on Cognitive Computing and Information Processing (CCIP) , pages 1–4, 2015. [17] Xin Li. Semantic integration over text: From ambiguous names to identiﬁable entities. 2004. [18] FA Mohammed. A knowledge based arabic question answering system (aqas). ACM SIGART Bulletin , 4(4):21–30, 1993. [19] Syed Mehedi Hasan Nirob. Question classiﬁcation using support vector machine with hybrid feature extraction method. In 2017 20th Interna- tional Conference of Computer and Information Technology (ICCIT) , pages 1–6, 2017. [20] Vladimir Pestov. Is the k-nn classiﬁer in high dimensions affected by the curse of dimensionality? Computers & Mathematics with Applications , 65(10):1427–1437, 2013. [21] John Prager. The use of predictive annotation for question answering in trec8. In In NIST Special Publication 500-246: The Eighth Text REtrieval Conference (TREC 8) , 1999. [22] Juan Ramos. Using tf-idf to determine word relevance in document queries. In Proceedings of the ﬁrst instructional conference on machine learning , volume 242, pages 133–142. Piscataway, NJ, 2003.
[23] Ellen M Voorhees. The trec-8 question answering track report. In Trec ,
volume 99, pages 77–82, 1999.
[24] Wilson Wong. Practical approach to knowledge-based question answer-
ing with natural language understanding and advanced reasoning. arXiv
preprint arXiv:0707.3559 , 2007.
[25] William Woods. The lunar sciences natural language information system.
BBN report , 1972.
[26] Zhang Yu.
Modiﬁed bayesian model based question classiﬁcation.
Journal of Chinese information processing , 19(2):100–105, 2005.
[27] LotﬁA Zadeh. From search engines to question answering systemsthe
problems of world knowledge, relevance, deduction and precisiation. In
Capturing Intelligence , volume 1, pages 163–210. Elsevier, 2006.
[28] Dell Zhang and Wee Sun Lee. Question classiﬁcation using support
vector machines. In Proceedings of the 26th annual international ACM
SIGIR conference on Research and development in informaion retrieval ,
pages 26–32, 2003.
[29] Zhiping Zheng. Answerbus question answering system. In Proceedings
of the second international conference on Human Language Technology Research , pages 399–404, 2002.

---

Question classiﬁcation (QC) deals with question analysis
and question labeling based on the expected answer type. The
goal of QC is to assign classes accurately to the questions
based on expected answer. In modern system, there are two
types of questions [14]. One is Factoid question which is
about providing concise facts and another one is Complex
question that has a presupposition which is complex. Question
Answering (QA) System is an integral part of our daily
life because of the high amount of usage of Internet for
information acquisition. In recent years, most of the research
works related to QA are based on English language such as
IBM Watson, Wolfram Alpha. Bengali speakers often fall in
difﬁculty while communicating in English [5].
In this research, we brieﬂy discuss the steps of QA system
and compare the performance of seven machine learning
based classiﬁers (Multi-Layer Perceptron (MLP), Naive Bayes
Classiﬁer (NBC), Support Vector Machine (SVM), Gradi-
ent Boosting Classiﬁer (GBC), Stochastic Gradient Descent
(SGD), K Nearest Neighbour (K-NN) and Random Forest
(RF)) in classifying Bengali questions to classes based on their
anticipated answers. Bengali questions have ﬂexible inquiring
ways, so there are many difﬁculties associated with Bengali
QC [14]. As there is no rich corpus of questions in Ben-
gali Language available, collecting questions is an additional
challenge. Different difﬁculties in building a QA System are
mentioned in the literature [11] [27]. The ﬁrst work on a
machine learning based approach towards Bengali question
classiﬁcation is presented in [14] that employ the Stochastic
Gradient Descent (SGD).
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Mentions 'our Bengali question corpus' but not the 3500 questions or their sources.

## CEC-28

**Question:** how is model compactness measured?

**Reference answer(s):** Using file size on disk ‖ 15.4 MB

<details><summary>Gold evidence</summary>

> Even if LangID-High does not present a more accurate result, it does present a more compact one: LangID-High is 15.4 MB, while the combined wFST high resource models are 197.5 MB.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
the em- beddings our source encoder learned for the lan- guage ID tokens showed anything similar. In a few cases they do (the languages closest to German in the vector space are Luxembourgish, Bavarian, and Yiddish, all close relatives). However, for the most part the structure of these vectors is not in- terpretable. Therefore, it would be difﬁcult to esti- mate the embedding for an unseen language, or to “borrow” the language ID token of a similar lan- guage. A more promising way forward is to ﬁnd a model that uses an externally constructed typolog- ical representation of the language. In contrast to the language embeddings, the phoneme embeddings appear to show many reg- ularities (see Table 8 ). This is a sign that our multilingual model learns similar embeddings for phonemes that are written with the same grapheme in different languages. These phonemes tend to be phonetically similar to each other. Perhaps the structure of the phoneme embed- ding space is what leads to our models’ very good performance on WER 100. Even when the model’s ﬁrst predicted pronunciation is not cor- rect, it tends to assign more probability mass to guesses that are more similar to the correct one. Applying some sort of ﬁltering or reranking of the system output might therefore lead to better per- formance. Phoneme Closest phonemes b p h , B , F @ ˜a , ˘e , W t h t: , t , t” x X , G , è y y: , Y , I ô R G , r” , R Table 8: Selected phonemes and the most similar phonemes, measured by the cosine similarity of the embeddings learned by the LangID-All model Because the language ID token is so beneﬁcial to performance, it would be very interesting to ﬁnd

---

languages writ- ten in the Latin alphabet. Given a short text in a language, the model predicts the language’s or- thographic rules. To create phonemic context fea- tures from the short text, the model na¨ıvely maps graphemes to IPA symbols written with the same character, and uses the features of these symbols to learn an approximation of the phonotactic con- straints of the language. In their experiments, these phonotactic features proved to be more valu- able than geographical and genetic features drawn from WALS ( Dryer and Haspelmath , 2013 ). In recent years, neural networks have emerged as a common way to use data from several languages in a single system. Google’s zero-shot neural ma- chine translation system ( Johnson et al. , 2016 ) shares an encoder and decoder across all language pairs. In order to facilitate this multi-way transla- tion, they prepend an artiﬁcial token to the begin- ning of each source sentence at both training and translation time. The token identiﬁes what lan- guage the sentence should be translated to. This approach has three beneﬁts: it is far more efﬁcient than building a separate model for each language pair; it allows for translation between languages that share no parallel data; and it improves re- sults on low-resource languages by allowing them to implicitly share parameters with high-resource languages. Our g2p system is inspired by this ap- proach, although it differs in that there is only one target “language”, IPA, and the artiﬁcial tokens identify the language of the source instead of the language of the target. Other work has also made use of multilingually- trained neural networks. Phoneme-level polyglot language models ( Tsvetkov et al. , 2016 ) train a single model on multiple languages and addition- ally condition on externally constructed typolog- ical data about

---

and the /ç/ in Kaninchen are instances of the same phoneme, so their phonemic representations should use the same symbol. However, the clean- ing algorithm can also have negative effects on the data quality. For example, the phoneme /ô/ is not present in the Phoible inventory for German, but it is used in several German transcriptions in the cor- pus. The cleaning algorithm converts /ô/ to /l/ in all German transcriptions, whereas /r/ would be a more reasonable guess. The cleaning algorithm also removes most suprasegmentals, even though these are often an important part of a language’s phonology. Developing a more sophisticated pro- cedure for cleaning pronunciation data is a direc- tion for future work, but in this paper we use the corpus’s provided cleaned transcriptions in order to ease comparison to previous results. Lang. Script Spelling Cleaned IPA Raw IPA deu Latin Ansbach a: n s b a: x "ansbaX deu Latin Kaninchen k a: n I n x @ n ka"ni:nç@n eus Latin untxi u n” t” S I "un. > tSi Table 3: Example entries from the Wiktionary training corpus We present experiments with two versions of our sequence-to-sequence model. LangID prepends each training, validation, and test sample with an artiﬁcial token identifying the language of the sample. NoLangID omits this token. LangID and NoLangID have identical structure otherwise. To translate the test corpus, we used a beam width of 100. Although this is an unusually wide beam and had negligible performance effects, it was neces- sary to compute our error metrics. We use the following three evaluation metrics: • Phoneme Error Rate (PER) is the Lev- enshtein distance between the predicted phoneme sequences and the gold standard phoneme sequences, divided by the length of the gold standard phoneme sequences. • Word Error Rate (WER) is the

---

low-resource scenarios. In International Work- shop on Spoken Language Technologies for Under- resourced Languages (SLTU) . pages 139–145. Yulia Tsvetkov, Sunayana Sitaram, Manaal Faruqui, Guillaume Lample, Patrick Littell, David Mortensen, Alan W Black, Lori Levin, and Chris Dyer. 2016. Polyglot neural language models: A case study in cross-lingual phonetic representation learning. In NAACL 2016 . San Diego, California, pages 1357–1366. Kaisheng Yao and Geoffrey Zweig. 2015. Sequence- to-sequence neural net models for grapheme- to-phoneme conversion. arXiv preprint arXiv:1506.00196 .
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) No model size (15.4 MB vs 197.5 MB) in context.

## CEC-29

**Question:** Which types of named entities do they recognize?

**Reference answer(s):** PER, LOC, ORG, MISC ‖ PER | LOC | ORG | MISC

<details><summary>Gold evidence</summary>

> The SnapCaptions dataset is composed of 10K user-generated image (snap) and textual caption pairs where named entities in captions are manually labeled by expert human annotators (entity types: PER, LOC, ORG, MISC). These captions are collected exclusively from snaps submitted to public and crowd-sourced stories (aka Snapchat Live Stories or Our Stories). Examples of such public crowd-sourced stories are “New York Story” or “Thanksgiving Story”, which comprise snaps that are aggregated for various public events, venues, etc. All snaps were posted between year 2016 and 2017, and do not contain raw images or other associated information (only textual captions and obfuscated visual descriptor features extracted from the pre-trained InceptionNet are available). We split the dataset into train (70%), validation (15%), and test sets (15%). The captions data have average length of 30.7 characters (5.81 words) with vocabulary size 15,733, where 6,612 are considered unknown tokens from Stanford GloVE embeddings BIBREF22 . Named entities annotated in the SnapCaptions dataset include many of new and emerging entities, and they are found in various surface forms (various nicknames, typos, etc.) To the best of our knowledge, SnapCaptions is the only dataset that contains natural image-caption pairs with expert-annotated named entities.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Social media with abundant user-generated posts
provide a rich platform for understanding events,
opinions and preferences of groups and individ-
uals. These insights are primarily hidden in un-
structured forms of social media posts, such as
in free-form text or images without tags. Named
entity recognition (NER), the task of recognizing
named entities from free-form text, is thus a criti-
cal step for building structural information, allow-
ing for its use in personalized assistance, recom-
mendations, advertisement, etc.
While many previous approaches ( Lample
et al. , 2016 ; Ma and Hovy , 2016 ; Chiu and
(a)
(b)
Figure 1:
Multimodal NER + modality attention .
(a) Visual contexts help recognizing polysemous entity
names (‘Monopoly’ as in a board game versus an eco-
nomics term). (b) Modality attention successfully sup-
presses word embeddings of a unknown token (‘Marsh-
melloooo’ with erroneously trailing ‘o’s), and focuses
on character-based context ( e.g. capitalized ﬁrst letter,
and lexical similarity to a known named entity (‘Marsh-
mello’, a music producer)) for correct prediction.
Nichols , 2015 ; Huang et al. , 2015 ) on NER have
shown success for well-formed text in recognizing
named entities via word context resolution ( e.g.
LSTM with word embeddings) combined with
character-level features ( e.g.
CharLSTM/CNN),
several additional challenges remain for recog-
nizing named entities from extremely short and
coarse text found in social media posts. For in-
stance, short social media posts often do not pro-
vide enough textual contexts to resolve polyse-

---

Bidi-
rectional lstm-crf models for sequence tagging.
arXiv:1508.01991 .
John Lafferty, Andrew McCallum, and Fernando CN
Pereira. 2001.
Conditional random ﬁelds: Prob-
abilistic models for segmenting and labeling se-
quence data .
Guillaume Lample, Miguel Ballesteros, Sandeep Sub-
ramanian, Kazuya Kawakami, and Chris Dyer. 2016.
Neural architectures for named entity recognition.
NAACL .
Xuezhe Ma and Eduard Hovy. 2016.
End-to-end
sequence labeling via bi-directional lstm-cnns-crf.
arXiv preprint arXiv:1603.01354 .
Andrew McCallum and Wei Li. 2003. Early results for
named entity recognition with conditional random
ﬁelds, feature induction and web-enhanced lexicons.
In NAACL .
Tomas Mikolov, Kai Chen, Greg Corrado, and Jeffrey
Dean. 2013. Efﬁcient estimation of word represen-
tations in vector space. ICLR .
Seungwhan Moon and Jaime Carbonell. 2017. Com-
pletely heterogeneous transfer learning with atten-
tion: What and what not to transfer. IJCAI .
Seungwhan Moon, Suyoun Kim, and Haohan Wang.
2015. Multimodal transfer deep learning with appli-
cations in audio-visual recognition. In NIPS MMML
Workshop .
Alexandre Passos, Vineet Kumar, and Andrew McCal-
lum. 2014. Lexicon infused phrase embeddings for
named entity resolution. aarXiv:1404.5367 .
Jeffrey Pennington, Richard Socher, and Christo-
pher D. Manning. 2014. Glove: Global vectors for
word representation. In EMNLP .
Lev Ratinov and Dan Roth. 2009. Design challenges
and misconceptions in named entity recognition. In
CoNLL .
Marek Rei, Gamal KO Crichton, and Sampo Pyysalo.
2016.
Attending to characters in neural sequence

---

Gustavo Aguilar, Suraj Maharjan, A. Pastor Lopez-
Monroy, and Thamar Solorio. 2017. A multi-task
approach for named entity recognition in social me-
dia data. ACL WNUT Workshop .
Stanislaw Antol, Aishwarya Agrawal, Jiasen Lu, Mar-
garet Mitchell, Dhruv Batra, C Lawrence Zitnick,
and Devi Parikh. 2015. Vqa: Visual question an-
swering. In ICCV .
Timothy
Baldwin,
Marie-Catherine
de
Marneffe,
Bo Han, Young-Bum Kim, Alan Ritter, and Wei
Xu. 2015. Shared tasks of the 2015 workshop on
noisy user-generated text: Twitter lexical normaliza-
tion and named entity recognition. In Proceedings
of the Workshop on Noisy User-generated Text .
William Chan, Navdeep Jaitly, Quoc V Le, and
Oriol Vinyals. 2015.
Listen, attend and spell.
arXiv:1508.01211 .
Jason PC Chiu and Eric Nichols. 2015.
Named
entity recognition with bidirectional lstm-cnns.
arXiv:1511.08308 .
Paramveer Dhillon, Dean P Foster, and Lyle H Ungar.
2011. Multi-view learning of word embeddings via
cca. In NIPS . pages 199–207.
John Duchi, Elad Hazan, and Yoram Singer. 2011.
Adaptive subgradient methods for online learning
and stochastic optimization. JMLR .
Desmond Elliott, Stella Frank, and Eva Hasler. 2015.
Multi-language image description with neural se-
quence models. CoRR, abs/1510.04709 .
Zhiheng Huang, Wei Xu, and Kai Yu. 2015.
Bidi-
rectional lstm-crf models for sequence tagging.
arXiv:1508.01991 .
John Lafferty, Andrew McCallum, and Fernando CN
Pereira. 2001.
Conditional random ﬁelds: Prob-
abilistic models for segmenting and labeling se-
quence data .
Guillaume Lample, Miguel Ballesteros, Sandeep Sub-

---

disambiguating polysemous entities, or to atten-
uate visual contexts when they are irrelevant to
target named entities, e.g . selﬁes, etc. Note that
the proposed modality attention module is distinct
from how attention is used in other sequence-to-
sequence literature ( e.g. attending to a speciﬁc to-
ken within an input sequence). Section 2 provides
the detailed literature review.
Our contributions are three-fold: we propose
(1) an LSTM-CNN hybrid multimodal NER net-
work that takes as input both image and text for
recognition of a named entity in text input. To the
best of our knowledge, our approach is the ﬁrst
work to incorporate visual contexts for named en-
tity recognition tasks. (2) We propose a general
modality attention module that selectively chooses
modalities to extract primary context from, max-
imizing information gain and suppressing irrele-
vant contexts from each modality (we treat words,
characters, and images as separate modalities). (3)
We show that the proposed approaches outperform
the state-of-the-art NER models ( both with and
without using additional visual contexts) on our
new MNER dataset SnapCaptions , a large collec-
tion of informal and extremely short social media
posts paired with unique images.

---

Table 1 shows the NER performance on the Snap
Captions dataset.
We report both entity types
recognition (PER, LOC, ORG, MISC) and named
entity segmentation (named entity or not) results.
Parameters : We tune the parameters of each
model with the following search space (bold in-
dicate the choice for our ﬁnal model): character
embeddings dimension: { 25, 50, 100, 150 , 200,
300 } , word embeddings size: { 25, 50, 100, 150 ,
200, 300 } , LSTM hidden states: { 25, 50, 100 ,
150, 200, 300 } , and x dimension: { 25, 50, 100,
150 , 200, 300 } . We optimize the parameters with
Adagrad ( Duchi et al. , 2011 ) with batch size 10,
learning rate 0.02, epsilon 10 − 8 , and decay 0.0.
Main Results : When visual context is available
(W+C+V), we see that the model performance
greatly improves over the textual models (W+C),
showing that visual contexts are complimentary
to textual information in named entity recognition
tasks. In addition, it can be seen that the modality
attention module further improves the entity type
recognition performance for (W+C+V). This re-
sult indicates that the modality attention is able
to focus on the most effective modality (visual,
words, or characters) adaptive to each sample to
maximize information gain. Note that our text-
only model (W+C) with the modality attention
module also signiﬁcantly outperform the state-of-
the-art baselines ( Aguilar et al. , 2017 ; Ma and
Hovy , 2016 ; Lample et al. , 2016 ) that use the same
textual modalities (W+C), showing the effective-
ness of the modality attention module for textual
models as well.
```
</details>

- **Judgment:** `[x] YES   [ ] NO   [ ] UNSURE`
- **Note (optional):** (Claude) 'entity types recognition (PER, LOC, ORG, MISC)' present.

## CEC-30

**Question:** What neural network modules are included in NeuronBlocks?

**Reference answer(s):** Embedding Layer | Neural Network Layers | Loss Function | Metrics

<details><summary>Gold evidence</summary>

> We recognize the following major functional categories of neural network components. Each category covers as many commonly used modules as possible. The Block Zoo is an open framework, and more modules can be added in the future.
> Embedding Layer: Word/character embedding and extra handcrafted feature embedding such as pos-tagging are supported.
> Neural Network Layers: Block zoo provides common layers like RNN, CNN, QRNN BIBREF2 , Transformer BIBREF3 , Highway network, Encoder Decoder architecture, etc. Furthermore, attention mechanisms are widely used in neural networks. Thus we also support multiple attention layers, such as Linear/Bi-linear Attention, Full Attention BIBREF4 , Bidirectional attention flow BIBREF5 , etc. Meanwhile, regularization layers such as Dropout, Layer Norm, Batch Norm, etc are also supported for improving generalization ability.
> Loss Function: Besides of the loss functions built in PyTorch, we offer more options such as Focal Loss BIBREF6 .
> Metrics: For classification task, AUC, Accuracy, Precision/Recall, F1 metrics are supported. For sequence labeling task, F1/Accuracy are supported. For knowledge distillation task, MSE/RMSE are supported. For MRC task, ExactMatch/F1 are supported.
> The Neuronblocks is built on PyTorch. The overall framework is illustrated in Figure FIGREF16 . It consists of two layers: the Block Zoo and the Model Zoo. In Block Zoo, the most commonly used components of deep neural networks are categorized into several groups according to their functions. Within each category, several alternative components are encapsulated into standard and reusable blocks with a consistent interface. These blocks serve as basic and exchangeable units to construct complex network architectures for different NLP tasks. In Model Zoo, the most popular NLP tasks are identified. For each task, several end-to-end network templates are provided in the form of JSON configuration files. Users can simply browse these configurations and choose one or more to instantiate. The whole task can be completed without any coding efforts.

</details>

<details><summary>Context (as the language model would receive it)</summary>

```text
Neuronblocks is built on PyTorch.
The overall
framework is illustrated in Figure 1 . It consists of
two layers: the Block Zoo and the Model Zoo . In
Block Zoo, the most commonly used components
of neural networks are categorized into several
groups according to their functions. Within each
category, several alternative components are en-
capsulated into standard and reusable blocks with
a consistent interface. These blocks serve as basic
and exchangeable units to construct complex net-
work architectures for different tasks. In Model
Zoo, the most popular NLP tasks are identiﬁed.
For each task, several end-to-end network tem-
plates are provided in the form of JSON conﬁgu-
ration ﬁles. Users can simply browse these conﬁg-
urations and choose one to instantiate. The whole
task can be completed without any coding efforts.

---

In this paper, we introduce NeuronBlocks, a DNN
toolkit for NLP tasks built on PyTorch, targeting
6 https://github.com/huggingface/
pytorch-transformers
Model
AUC
CNN ( ( Yang et al. , 2015 ))
73.59
CNN-Cnt ( ( Yang et al. , 2015 ))
75.33
CNN (NeuronBlocks)
74.79
BiLSTM (NeuronBlocks)
76.73
BiLSTM+Attn (NeuronBlocks)
75.48
BiLSTM+MatchAttn (NeuronBlocks)
78.54
Table 5: NeuronBlocks results on WikiQA.
three types of engineers, and provides a two-layer
solution to satisfy the requirements from all three
types of users. To be more speciﬁc, the Model Zoo
consists of various templates for the most com-
mon NLP tasks, while the Block Zoo supplies a
gallery of alternative layers/modules for the net-
works. Such design achieves a balance between
generality and ﬂexibility. Extensive experiments
have veriﬁed the effectiveness of this approach.
NeuronBlocks has been widely used in a product
team of a commercial search engine, and signif-
icantly improved the productivity for developing
NLP DNN approaches.
As an open-source toolkit, we will further ex-
tend it in various directions. The following names
a few examples.
• Multi-task learning (MTL). In MTL, multiple
related tasks are jointly trained so that knowl-
edge learned in one task can beneﬁt other tasks.
• Pre-training and ﬁne-tuning. Deep pre-training
models such as ELMo ( Peters et al. , 2018 ),
GPT ( Radford et al. , 2018 ), BERT ( Devlin
et al. , 2019 ) are new directions in NLP.
• Sequence generation task.
Sequence genera-
tion is widely used in NLP ﬁelds such as ma-
chine translation ( Bahdanau et al. , 2015 ), text

---

In NeuronBlocks, we identify four types of most
popular NLP tasks. For each task, we provide var-
ious end-to-end network templates.
• Text Classiﬁcation and Matching . Tasks such
as domain/intent classiﬁcation, question an-
swer matching are supported.
• Sequence Labeling . Predict each token in a
sequence into predeﬁned types. Common tasks
include NER, POS tagging, Slot tagging, etc.
• Knowledge Distillation ( Hinton et al. , 2015 ).
Teacher-Student based knowledge distillation
is one common approach for model com-
pression.
NeuronBlocks provides knowledge
distillation template to train light-weight stu-
dent model to imitate heavy DNN models like
BERT/GPT.
• Extractive Machine Reading Comprehen-
sion . Given question and passage, this task is
to predict the start and end positions of the an-
swer spans in the passage.

---

reusable and standard components, which can be
adopted as building blocks to construct networks
with complex architecture. By following the in-
terface guidelines, users can also contribute to this
gallery of components with their own modules.
The technical contributions of NeuronBlocks
are summarized into the following three aspects.
• Block Zoo : categorize and abstract the most
commonly used DNN components into stan-
dard and reusable blocks. The blocks within
the same category can be used exchangeably.
• Model Zoo : identify the most popular NLP
tasks and provide alternative end-to-end net-
work templates (in JSON format) for each task.
• Platform Compatibility : support both Linux
and Windows machines, CPU/GPU chips, as
well as GPU platforms such as PAI 3 .
3 https://github.com/Microsoft/pai

---

NeuronBlocks provides convenient user interface 4
for users to build, train, and test DNN models. The
details are described in the following.
• I/O interface .
This part deﬁnes model in-
put/output, such as training data, pre-trained
models/embeddings, model saving path, etc.
• Model Architecture interface . This is the key
part of the conﬁguration ﬁle, which deﬁnes the
whole model architecture. Figure 2 shows an
example of how to specify a model architecture
using the blocks in NeuronBlocks. To be more
speciﬁc, it consists of a list of layers/blocks to
construct the architecture, where the blocks are
supplied in the gallery of Block Zoo .
• Training Parameters interface . In this part,
the model optimizer as well as all other training
hyper parameters are indicated.
3.4
Workﬂow
Figure 3 shows the workﬂow of building DNN
models in NeuronBlocks. Users only need to write
a JSON conﬁguration ﬁle. They can either instan-
tiate an existing template from Model Zoo , or con-
struct a new architecture based on the blocks from
Block Zoo . This conﬁguration ﬁle is shared across
training, test, and prediction.
For model hyper-parameter tuning or architec-
ture modiﬁcation, users just need to change the
JSON conﬁguration ﬁle. Advanced users can also
contribute novel customized blocks 5 into Block
Zoo , as long as they follow the same interface
guidelines with the existing blocks. These new
blocks can be further shared across all users for
model architecture design.
Moreover, Neuron-
Blocks has ﬂexible platform support, such as
GPU/CPU, GPU management platforms like PAI.
```
</details>

- **Judgment:** `[ ] YES   [x] NO   [ ] UNSURE`
- **Note (optional):** (Claude) Block Zoo described generically; the four categories (Embedding, NN layers, Loss, Metrics) not listed.
