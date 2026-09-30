"""命令行入口：跑公会研究样例。"""

import argparse

from .core import Research


def build_parser():
    parser = argparse.ArgumentParser(prog="guild-research", description="公会研究")
    parser.add_argument("--sample", default="slots", help="slots / time / dup / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "slots":
        book = Research(slots=2)
        results = [book.start("r-%d" % index, 5000, 0) for index in range(3)]
        print("third=%s running=%d" % (str(results[2]).lower(), book.running()))
    elif args.sample == "time":
        book = Research(slots=2)
        book.start("r-1", 5000, 0)
        book.advance(1000)
        book.advance(6000)
        print("done=%d" % len(book.done))
    elif args.sample == "dup":
        book = Research(slots=2)
        first = book.start("r-1", 5000, 0)
        second = book.start("r-1", 5000, 10)
        print("second=%s running=%d" % (str(second).lower(), book.running()))
    elif args.sample == "scan":
        book = Research(slots=100000)
        for index in range(3000):
            book.start("r-%d" % index, 5000, 0)
        for _ in range(3000):
            book.running()
        print("scanned=%d" % book.scanned_count())
    else:
        raise SystemExit("需要 --sample slots|time|dup|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
