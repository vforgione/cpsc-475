#!/usr/bin/env python3

import codecs
import csv
import os
from argparse import ArgumentParser
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import jinja2


MINIMUM_LOAD = 720  # 12 hours

EXPECTED_ATTENDANCE = 4
EXPECTED_DISCUSSION = 4

TASK_VALUE = 33
PR_VALUE = 33

ATTENDANCE_VALUE = 7
DISCUSSION_VALUE = 7
REVIEW_VALUE = 20

GRP_TASK_VALUE = 34
GRP_PR_VALUE = 33
GRP_TEST_VALUE = 33

TEMPLATE = os.path.join(os.path.dirname(__file__), 'templates', 'report.html.j2')


def read_csv(filename: str, delimiter: str=',') -> List[dict]:
    fieldnames = ['task_id', 'pr_id', 'assignee', 'state', 'task_points', 'reviewers', 'attendance', 'discussion']
    with codecs.open(filename=filename, mode='r', encoding='utf8') as fh:
        reader = csv.DictReader(fh, fieldnames=fieldnames, delimiter=delimiter)
        return [row for row in reader]


def tabulate_by_assignee_type_state(rows: List[dict]) -> Dict[str, Dict[str, Dict[str, int]]]:
    assignee_type_state = defaultdict(lambda: defaultdict(Counter))
    for row in rows:
        assignee = row['assignee']
        if not assignee:
            continue

        state = str(row['state']).lower()

        if row['task_id']:
            points = row['task_points']
            if not points:
                continue
            points = float(points)

            assignee_type_state[assignee]['tasks'][state] += points

        elif row['reviewers']:
            assignee_type_state[assignee]['prs'][state] += 1

            reviewers = str(row['reviewers']).split(',')
            for reviewer in reviewers:
                assignee_type_state[reviewer]['reviews']['reviews'] += 1

        elif row['attendance'] and row['discussion']:
            assignee_type_state[assignee]['attendance']['attendance'] = int(row['attendance'])
            assignee_type_state[assignee]['discussion']['discussion'] = int(row['attendance'])

    return assignee_type_state


def total_assignee_type(assignee_types: Dict[str, Dict[str, Dict[str, int]]]) -> None:
    for assignee, type_state in assignee_types.items():
        for pt_type, state_map in type_state.items():
            assignee_types[assignee][pt_type]['total'] = sum(state_map.values())


def compute_averages(assignee_types: Dict[str, Dict[str, Dict[str, int]]]) -> Tuple[float, float, float]:
    tasks, prs, reviews = 0, 0, 0
    for assignee, type_state in assignee_types.items():
        tasks += type_state['tasks']['total']
        prs += type_state['prs']['total']
        reviews += type_state['reviews']['total']

    tasks /= len(assignee_types)
    prs /= len(assignee_types)
    reviews /= len(assignee_types)
    return tasks, prs, reviews


def compute_individual_scores(
        assignee_types: Dict[str, Dict[str, Dict[str, int]]],
        grp_avg_tasks: float,
        grp_avg_prs: float,
        grp_avg_reviews: float) -> None:

    if grp_avg_tasks < MINIMUM_LOAD:
        grp_avg_tasks = MINIMUM_LOAD

    for assignee, type_state in assignee_types.items():
        # tasks
        closed_tasks = type_state['tasks'].get('closed', 0)
        total_tasks = type_state['tasks'].get('total', 0)
        if total_tasks:
            task_close_rate = closed_tasks / total_tasks
            task_multiplier = closed_tasks / grp_avg_tasks
            task_rate = task_close_rate * task_multiplier
        else:
            task_rate = 0
            task_multiplier = 0
            task_close_rate = 0

        assignee_types[assignee]['tasks']['score'] = task_rate * TASK_VALUE
        assignee_types[assignee]['tasks']['multiplier'] = task_multiplier
        assignee_types[assignee]['tasks']['avg'] = grp_avg_tasks
        assignee_types[assignee]['tasks']['close_rate'] = task_close_rate

        # prs
        merged_prs = type_state['prs'].get('merged', 0)
        total_prs = type_state['prs'].get('total', 0)
        if total_prs:
            merge_rate = merged_prs / total_prs
        else:
            merge_rate = 0

        assignee_types[assignee]['prs']['score'] = merge_rate * PR_VALUE
        assignee_types[assignee]['prs']['avg'] = grp_avg_prs
        assignee_types[assignee]['prs']['merge_rate'] = merge_rate

        # participation
        attendance = assignee_types[assignee]['attendance'].get('total', 0)
        discussion = assignee_types[assignee]['discussion'].get('total', 0)
        reviews = assignee_types[assignee]['reviews'].get('total', 0)

        att_rate = attendance / EXPECTED_ATTENDANCE * ATTENDANCE_VALUE
        disc_rate = discussion / EXPECTED_DISCUSSION * DISCUSSION_VALUE
        pr_rate = reviews / grp_avg_reviews * REVIEW_VALUE
        participation = att_rate + disc_rate + pr_rate

        assignee_types[assignee]['participation']['score'] = participation
        assignee_types[assignee]['reviews']['avg'] = grp_avg_reviews

        # total
        assignee_types[assignee]['total']['score'] = \
            assignee_types[assignee]['tasks']['score'] + \
            assignee_types[assignee]['prs']['score'] + \
            assignee_types[assignee]['participation']['score']


def compute_base_group_score(
        assignee_types: Dict[str, Dict[str, Dict[str, int]]],
        real_tests: int,
        expected_tests: int) -> Dict[str, float]:

    total_tasks, closed_tasks, total_prs, merged_prs = 0, 0, 0, 0
    for assignee, type_state in assignee_types.items():
        total_tasks += type_state['tasks']['total']
        closed_tasks += type_state['tasks']['closed']
        total_prs += type_state['prs']['total']
        merged_prs += type_state['prs']['merged']

    task_rate = closed_tasks / total_tasks
    pr_rate = merged_prs / total_prs
    test_rate = real_tests / expected_tests

    task_score = task_rate * GRP_TASK_VALUE
    pr_score = pr_rate * GRP_PR_VALUE
    test_score = test_rate * GRP_TEST_VALUE
    total = task_score + pr_score + test_score

    return {
        'task_rate': task_rate,
        'pr_rate': pr_rate,
        'test_rate': test_rate,
        'task_score': task_score,
        'pr_score': pr_score,
        'test_score': test_score,
        'total': total,
    }


def _find_bound(value):
    rem = value % 10
    if rem < 5:
        return int(value / 10) * 10
    else:
        return int((value + 10) / 10) * 10


def compute_individual_group_score(
        assignee_types: Dict[str, Dict[str, Dict[str, int]]],
        total_group_score: float) -> None:

    for assignee, type_state in assignee_types.items():
        grp_multiplier = min([_find_bound(type_state['total']['score']) / 100, 1])
        assignee_types[assignee]['group']['score'] = grp_multiplier * total_group_score
        assignee_types[assignee]['group']['potential'] = total_group_score
        assignee_types[assignee]['group']['multiplier'] = grp_multiplier
        print('{}: {} because {} * {}'.format(assignee, grp_multiplier * total_group_score, grp_multiplier, total_group_score))


def render_report(
        assignee_types: Dict[str, Dict[str, Dict[str, int]]],
        group_score: Dict[str, float],
        grp_avg_tasks: float,
        grp_avg_prs: float,
        grp_avg_reviews: float,
        output: str) -> None:

    path, filename = os.path.split(TEMPLATE)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(path or './'))

    context = {
        'assignee_types': assignee_types,
        'replaced_avg_tasks': grp_avg_tasks < MINIMUM_LOAD,
        'avg_tasks': grp_avg_tasks,
        'avg_prs': grp_avg_prs,
        'avg_reviews': grp_avg_reviews,
        'group_score': group_score,
    }
    rendering = env.get_template(filename).render(context)
    with codecs.open(filename=output, mode='w', encoding='utf8') as fh:
        fh.write(rendering)


if __name__ == '__main__':
    import json

    parser = ArgumentParser()
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output')
    parser.add_argument('-r', '--real-tests', type=int)
    parser.add_argument('-e', '--expected-tests', type=int)
    args = parser.parse_args()

    query_rows = read_csv(args.input)
    student_map = tabulate_by_assignee_type_state(query_rows)
    total_assignee_type(student_map)
    avg_tasks, avg_prs, avg_reviews = compute_averages(student_map)
    compute_individual_scores(student_map, avg_tasks, avg_prs, avg_reviews)
    group_scores = compute_base_group_score(student_map, args.real_tests, args.expected_tests)

    compute_individual_group_score(student_map, group_scores['total'])

    # render_report(student_map, group_scores, avg_tasks, avg_prs, avg_reviews, args.output)
    # print(json.dumps(student_map, indent=2))
