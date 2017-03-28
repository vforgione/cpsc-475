import codecs
import csv
from argparse import ArgumentParser
from typing import Dict, List, Tuple


def read_csv(filename: str, fieldnames: List[str], delimiter: str) -> List[Dict[str, str]]:
    with codecs.open(filename=filename, mode='r', encoding='utf8') as fh:
        reader = csv.DictReader(fh, fieldnames=fieldnames, delimiter=delimiter)
        return [row for row in reader]


def write_joined_csv(
        filename: str,
        fieldnames: List[str],
        delimiter: str,
        rows: Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]) -> None:
    with codecs.open(filename=filename, mode='w', encoding='utf8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter=delimiter)
        for group in rows:
            writer.writerows(group)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-t', '--task-csv')
    parser.add_argument('-p', '--pr-csv')
    parser.add_argument('-c', '--class-csv')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()

    task_fieldnames = ['task_id', 'title', 'assignee', 'task_points', 'state']
    pr_fieldnames = ['assignee', 'pr_id', 'state', 'reviewers']
    class_fieldnames = ['assignee', 'attendance', 'discussion']

    task_rows = read_csv(filename=args.task_csv, fieldnames=task_fieldnames, delimiter='\t')
    pr_rows = read_csv(filename=args.pr_csv, fieldnames=pr_fieldnames, delimiter=',')
    class_rows = read_csv(filename=args.class_csv, fieldnames=class_fieldnames, delimiter=',')

    for row in task_rows:
        del row['title']

    joined_fieldnames = [
        'task_id', 'pr_id', 'assignee', 'state', 'task_points', 'reviewers', 'attendance', 'discussion']
    write_joined_csv(
        filename=args.output, fieldnames=joined_fieldnames, delimiter=',', rows=(task_rows, pr_rows, class_rows))
