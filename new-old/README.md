# CPSC 475

Scripts to speed up grading.

## Usage

This is a Python 3.6 application - you're going to need that to run this.

You're also going to need `jinja2` installed. I recommend creating a _virtualenv_ and `pip` installing it via the 
`requirements.txt` file.

Once you have those, you're going to need to create 3 source CSVs per sprint:

##### csvs/class/sprint-{n}.csv

The class CSV is really simple. It has only 3 fields: `assignee`, `attendance` and `discussion`. This is taken 
directly from the grade book. For example:

```plaintext
alice,4,4
bob,4,4
chuck,4,3
darth,2,2
```

In this case, alice and bob came to all 4 meetings and participated constructively in them;
chuck came to all 4, but sat quietly for one of them;
darth missed 2 meetings.

##### csvs/tasks/sprint-{n}.tsv

This one requires having a query saved in Team Services, then exporting the results to email, then copy/pasting 
the results from the email body into a TSV.

The keys for this are: `task_id`, `title`, `assignee`, `task_points` and `state`. For example

```plaintext
1,some task 1,alice,300,closed
2,some task 2,bob,300,closed
3,some task 3,alice,600,closed
4,some task 4,chuck,240,closed
5,some task 5,darth,180,closed
6,some task 6,darth,300,active
```

##### csvs/prs/sprint-{n}.csv

This is probably the biggest pain - you're going to need to manually go through all the pull requests in Team
Services and compile this CSV.

The keys for this are: `assignee`, `pr_id`, `state` and `reviewers`. For example:

```plaintext
alice,1,merged,"bob,chuck"
alice,2,merged,"bob,darth"
bob,3,merged,"alice,chuck"
chuck,4,merged,"bob,alice"
darth,5,abandoned,"bob,chuck"
darth,6,merged,"alice,chuck"
```

The last value could be a list of reviews separated by a comma - you'll have to surround it with quotes.

##### Joining the CSVs

Once you have the CSVs, you're going to need to join them into one big CSV. Use the `join-csvs.py` script:

```bash
$ source venv/bin/active
$ python join-csvs.py -t csvs/tasks/sprint-n.tsv -p csvs/prs/sprint-n.csv -c csvs/class/sprint-n.csv -o csvs/joined/sprint-n.csv
```

where `-t` is the path to the tasks CSV, `-p` is the PRs CSV, `-c` is the class CSV and `-o` is the output path.

##### Grading

Now that you have your mega-CSV, you can run the grading script:

```bash
$ source venv/bin/activate
$ python grade.py -i csvs/joined/sprint-n.csv -o reports/sprint-n.html -r 70 -e 75
```

where `-i` is the path to the input joined CSV, `-o` is the report output, `-r` is the real test coverage and 
`-e` is the expected test coverage.
 
The output of this script is an HTML file with high level scores and detailed break down. 
