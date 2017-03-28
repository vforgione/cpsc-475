import codecs
import csv
import logging
from collections import defaultdict
from typing import List


logging.basicConfig(format='%(levelname)s: %(message)s')


class Task:
    def __init__(self, task_id: int, name: str, points: int, status: str):
        self.task_id: int = task_id
        self.name: str = name
        self.points: int = points
        self.status: str = status


class TaskLoad:
    def __init__(self, assignee: str, tasks: List[Task]=None):
        self.assignee: str = assignee
        self.tasks: List[Task] = tasks or []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    @property
    def total_points(self) -> int:
        return sum(task.points for task in self.tasks)

    @property
    def closed_task_points(self) -> int:
        return sum(task.points for task in self.tasks if task.status == 'closed')

    @property
    def close_rate(self) -> float:
        if self.total_points:
            return self.closed_task_points / self.total_points
        return 0


def read_tasks_csv(filename) -> List[TaskLoad]:
    collated = defaultdict(list)
    assignee_tasks: List[TaskLoad] = []

    with codecs.open(filename, mode='r', encoding='utf8') as fh:
        reader = csv.reader(fh, delimiter='\t')
        for row in reader:
            task_id = row[0]
            name = row[1]
            assignee = row[2] or 'Unassigned'
            points = row[3]
            status = str(row[4]).lower()

            try:
                task_id = int(task_id)
            except ValueError:
                logging.error(f'could not get task_id from {row}')
                task_id = 99999999
            try:
                points = int(points)
            except ValueError:
                logging.error(f'could not get points from {row}')
                points = 0

            collated[assignee].append((task_id, name, points, status))

    for assignee, task_list in collated.items():
        load = TaskLoad(assignee)
        for _task in task_list:
            task = Task(*_task)
            load.add_task(task)
        assignee_tasks.append(load)

    return assignee_tasks


if __name__ == '__main__':
    import sys
    fname = sys.argv[1]
    for tl in read_tasks_csv(fname):
        print(f'{tl.assignee}: {tl.closed_task_points}/{tl.total_points}={tl.close_rate}')
