if __name__ == "__main__":
    with open("qrels.ohsu.88-91.r", "w") as f:
        with open("qrels.ohsu.88-91", "r") as r:
            for line in r:
                line = line.strip()
                if line:
                    sections = line.strip().split("\t")
                    sections.insert(1, "0")
                    f.write('\t'.join(sections) + "\n")