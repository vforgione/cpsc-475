import codecs
import csv
import logging
from collections import defaultdict
from typing import List


logging.basicConfig(format='%(levelname)s: %(message)s')


class PR:
    def __init__(self, pr_id: int, status: str):
        self.pr_id: int = pr_id
        self.status: str = status


class PrLoad:
    def __init__(self, creator: str, prs: List[PR]=None):
        self.creator: str = creator
        self.prs: List[PR] = prs or []

    def add_pr(self, pr: PR) -> None:
        self.prs.append(pr)

    @property
    def total_prs(self) -> int:
        return len(self.prs)

    @property
    def merged_prs(self) -> int:
        return len([pr for pr in self.prs if pr.status == 'merged'])

    @property
    def merge_rate(self) -> float:
        if self.total_prs:
            return self.merged_prs / self.total_prs
        return 0


def read_pr_csv(filename) -> List[PrLoad]:
    collation = defaultdict(list)
    creator_prs: List[PrLoad] = []

    with codecs.open(filename, mode='r', encoding='utf8') as fh:
        reader = csv.reader(fh, delimiter=',')
        for row in reader:
            person = row[0]
            pr_id = row[1]
            status = str(row[2]).lower()

            try:
                pr_id = int(pr_id)
            except ValueError:
                logging.error(f'could not get pr_id from {row}')
                pr_id = 99999999

            collation[person].append((pr_id, status))

        for creator, id_status in collation.items():
            load = PrLoad(creator)
            for pr_id, status in id_status:
                pr = PR(pr_id, status)
                load.add_pr(pr)
            creator_prs.append(load)

        return creator_prs


if __name__ == '__main__':
    import sys
    fname = sys.argv[1]
    for prl in read_pr_csv(fname):
        print(f'{prl.creator}: {prl.merged_prs}/{prl.total_prs}={prl.merge_rate}')
