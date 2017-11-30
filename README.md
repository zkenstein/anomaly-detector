- Az **erdos.inf.elte.hu**-t használhatom tesztelésre.
- `python detect_anomaly.py -h`, de egy példa: `python detect_anomaly.py --training ~/big-data-repository/milano/cdr/2013-11 --testing ~/big-data-repository/milano/cdr/2013-12 --square_from 1 --square_to 2 --action visualize`
- `python3 detect_anomaly.py --training /mnt/disk2/tim-bd-challenge/milano-november/ --testing /mnt/disk2/tim-bd-challenge/milano-december/ --square_from 1 --square_to 2 --action save > log1000.txt 2>&1`
- `npm run serve:dev` (development), `npm run serve` (production)
- 5855, 5856, 5955, 5956

# TODO

- Fejlesztői dokumentáció / Megoldási terv megírása
- Fejlesztői dokumentáció / Megvalósítás megírása
- Fejlesztői dokumentáció / Tesztelés megírása
- Word-be áttenni a megírt szöveget és az elvárt formai követelmények szerint megformázni
- Legkésőbb december 11 délelőtt elküldeni a konzulensnek
- Fejleszteni a doksit az alapján, amit a konzulens mond
- December 15-ig le kell adnom a szakdolgozatot

# Események

San siro: https://en.wikipedia.org/wiki/2013%E2%80%9314_A.C._Milan_season, https://www.uefa.com/uefachampionsleague/season=2014/matches/round=2000479/match=2011845/postmatch/index.html
- 1. 15:00 (Inter - Sampdoria)
- 8. 20:45 (Inter - Parma)
- 11. 20:45 (Milan - Ajax)
- 15. 20:45 (Milan - Roma)
- 22. 20:45 (Inter - Milan)

Teatro alla Scala: https://www.opera-online.com/en/items/productions/la-traviata-teatro-alla-scala-2013-2014-2013
December 07, 2013 18:00:00
December 12, 2013 20:00:00
December 15, 2013 20:00:00
December 18, 2013 20:00:00
December 22, 2013 15:00:00
December 28, 2013 20:00:00
December 31, 2013 18:00:00

The Feast of St. Ambrose: http://www.hotelwindsormilan.com/en/the-feast-of-st-ambrose-patron-of-milan/

# Anomaly Detector

Searching anomalies in call detail records ([CDR](https://en.wikipedia.org/wiki/Call_detail_record)). It's my BSc thesis. You can check the announcement at `docs/thesis-announcement.pdf`.

## Dataset

Telecom Italia's data. Recorded in Milano in 2013 november and september. You can download the dataset from [here](https://dandelion.eu/datamine/open-big-data/). It licensed under [ODbL](https://opendatacommons.org/licenses/odbl/).

### Description

From *dandelion.eu*:

> This dataset provides information about the telecommunication activity over the city.
>
> The dataset is the result of a computation over the Call Detail Records (CDRs) generated by the Telecom Italia cellular network over the city. CDRs log the user activity for billing purposes and network management. There are many types of CDRs, for the generation of this dataset we considered those related to the following activities:
>- Received SMS: a CDR is generated each time a user receives an SMS
>- Sent SMS: a CDR is generated each time a user sends an SMS
>- Incoming Calls: a CDR is generated each time a user receives a call
>- Outgoing Calls: CDR is generated each time a user issues a call
>- Internet: a CDR is generate each time
>	- a user starts an internet connection
>	- a user ends an internet connection
>	- during the same connection one of the following limits is reached:​
>		- 15 minutes from the last generated CDR
>		- 5 MB from the last generated CDR
>
> By aggregating the aforementioned records it was created this dataset that provides SMSs, calls and Internet traffic activity. It measures the level of interaction of the users with the mobile phone network; for example the higher is the number of SMS sent by the users, the higher is the activity of the sent SMS. Measurements of call and SMS activity have the same scale (therefore are comparable); those referring to Internet traffic do not.

#### Schema

From *dandelion.eu*:

>1. **Square id**: The id of the square that is part of the city GRID.
>2. **Time interval**: The beginning of the time interval expressed as the number of millisecond elapsed from the Unix Epoch on January 1st, 1970 at UTC. The end of the time interval can be obtained by adding 600000 milliseconds (10 minutes) to this value.
>3. **Country code**: The phone country code of a nation. Depending on the measured activity this value assumes different meanings that are explained later.
>4. **SMS-in activity**: The activity in terms of received SMS inside the Square id, during the Time interval and sent from the nation identified by the Country code.
>5. **SMS-out activity**: The activity in terms of sent SMS inside the Square id, during the Time interval and received by the nation identified by the Country code.
>6. **Call-in activity**: The activity in terms of received calls inside the Square id, during the Time interval and issued from the nation identified by the Country code.
>7. **Call-out activity**: The activity in terms of issued calls inside the Square id, during the Time interval and received by the nation identified by the Country code.
>8. **Internet traffic activity**: The activity in terms of performed internet traffic inside the Square id, during the Time interval and by the nation of the users performing the connection identified by the Country code.

#### File Format

From *dandelion.eu*:

>Files are in tsv format. If no activity was recorded for a field specified in the schema above then the corresponding value is missing from the file. For example, if for a given combination of the Square id `s`, the Time interval `i` and the Country code `c` no SMS was sent the corresponding record looks as follows:
>`s \t i \t c \t \t SMSout \t Callin \t Callout \t Internettraffic`
>where `\t` corresponds to the tab character, `SMSout` is the value corresponding to the SMS-out activity, `Callin` is the value corresponding to the Call-in activity, `Callout` is the value corresponding to the Call-out activity and `internettraffic` is the value corresponding to the  Internet traffic activity.
>
>Moreover, if for a given combination of the Square id `s`, the Time interval `i` and the Country code `c` no activity is recorded the corresponding record is missing from the dataset. This means that records of the following type
>`s \t i \t c \t \t \t \t \t`
>are not stored in the dataset.
