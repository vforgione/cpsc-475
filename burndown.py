#!/usr/bin/env python3

import codecs
import csv
from argparse import ArgumentParser
from collections import Counter, defaultdict
from typing import Dict, List


MINIMUM_LOAD = 720  # 12 hours


def read_csv(filename: str, delimiter: str='\t') -> List[dict]:
    fieldnames = ['task_id', 'title', 'assignee', 'task_points', 'state']
    with codecs.open(filename=filename, mode='r', encoding='utf8') as fh:
        reader = csv.DictReader(fh, fieldnames=fieldnames, delimiter=delimiter)
        return [row for row in reader]


def tabulate_by_assignee_type_state(rows: List[dict]) -> Dict[str, Dict[str, Dict[str, int]]]:
    assignee_type_state = defaultdict(lambda: defaultdict(Counter))
    for row in rows:
        assignee = row['assignee']
        if not assignee:
            assignee = 'Unclaimed!!!'

        state = str(row['state']).lower()

        if row['task_id']:
            points = row['task_points']
            if not points:
                points = 0
            points = float(points)

            assignee_type_state[assignee]['tasks'][state] += points

    return assignee_type_state


def total_assignee_type(assignee_types: Dict[str, Dict[str, Dict[str, int]]]) -> None:
    for assignee, type_state in assignee_types.items():
        for pt_type, state_map in type_state.items():
            assignee_types[assignee][pt_type]['total'] = sum(state_map.values())


def compute_averages(assignee_types: Dict[str, Dict[str, Dict[str, int]]]) -> float:
    tasks = 0
    for assignee, type_state in assignee_types.items():
        tasks += type_state['tasks']['total']

    tasks /= len(assignee_types)
    return tasks


def compute_individual_scores(
        assignee_types: Dict[str, Dict[str, Dict[str, int]]],
        grp_avg_tasks: float) -> None:

    if grp_avg_tasks < MINIMUM_LOAD:
        grp_avg_tasks = MINIMUM_LOAD

    for assignee, type_state in assignee_types.items():
        closed_tasks = type_state['tasks'].get('closed', 0)
        total_tasks = type_state['tasks'].get('total', 0)
        if total_tasks:
            task_close_rate = closed_tasks / total_tasks
        else:
            task_close_rate = 0

        assignee_types[assignee]['tasks']['avg'] = grp_avg_tasks
        assignee_types[assignee]['tasks']['close_rate'] = task_close_rate

        # total
        assignee_types[assignee]['total']['score'] = assignee_types[assignee]['tasks']['score']


if __name__ == '__main__':
    import json

    parser = ArgumentParser()
    parser.add_argument('-i', '--input')
    args = parser.parse_args()

    query_rows = read_csv(args.input)
    student_map = tabulate_by_assignee_type_state(query_rows)
    total_assignee_type(student_map)
    avg_tasks = compute_averages(student_map)

    print('Avg Tasks: {}'.format(avg_tasks))
    print(json.dumps(student_map, indent=2))
