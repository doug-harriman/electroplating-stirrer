from invoke import task
import os

# To see list of supported commands:
# >> invoke --list

DOC_PRE_FILENAME = ".doc.pre.json"
DOC_POST_FILENAME = ".doc.post.json"


def file_times(path: str = None) -> dict:
    """
    Captures list of files and modification times to dictionary.
    """

    if path is None:
        raise ValueError("path must be specified.")

    # Get list of files in current directory
    curdir = os.getcwd()
    os.chdir(path)
    files = os.listdir()

    # Create dictionary of file names and modification times
    results = {}
    results["directory"] = path
    file_dict = {}
    for file in files:
        file_dict[file] = os.path.getmtime(file)
    os.chdir(curdir)
    results["files"] = file_dict

    return results


@task
def doc_pre(ctx, path: str = None):
    """
    Captures list of files and modification times to a JSON file.
    """

    import json
    import sys

    if path is None:
        path = os.getcwd()

    # Write dictionary to file
    data = file_times(path=path)

    # Capture command line used to call simulation.
    data["command"] = os.path.basename(" ".join(sys.argv))

    with open(DOC_PRE_FILENAME, "w") as fp:
        json.dump(data, fp, indent=4)

    if os.path.isfile(DOC_POST_FILENAME):
        os.remove(DOC_POST_FILENAME)


@task
def doc(ctx):
    """
    Generates simulation result documentation (Work in progress)
    """
    import json
    from repo import Repo

    if not os.path.isfile(DOC_PRE_FILENAME):
        raise Exception("doc_pre() must be run before doc(), or: inv doc-pre")

    with open(DOC_PRE_FILENAME, "r") as fp:
        data = json.load(fp)

    pre = data["files"]
    post = file_times(path=data["directory"])["files"]

    # Generate list of new and modified files
    files_mod = list(set(post.keys()) - set(pre.keys()))
    for file in post.keys():
        if file in pre.keys():
            if post[file] > pre[file]:
                files_mod.append(file)
    files_mod.sort()
    if DOC_PRE_FILENAME in files_mod:
        files_mod.remove(DOC_PRE_FILENAME)
    if DOC_POST_FILENAME in files_mod:
        files_mod.remove(DOC_POST_FILENAME)
    data["files"] = files_mod

    # Nice output
    data = dict(sorted(data.items()))

    # Analysis may have dumped data, create or update
    if not os.path.isfile(DOC_POST_FILENAME):
        # Create new file
        with open(DOC_POST_FILENAME, "w") as fp:
            json.dump(data, fp, indent=4)
    else:
        # Update existing file
        with open(DOC_POST_FILENAME, "r") as fp:
            doc_existing = json.load(fp)
        doc_existing.update(data)
        with open(DOC_POST_FILENAME, "w") as fp:
            json.dump(doc_existing, fp, indent=4)


if __name__ == "__main__":
    from invoke import Context

    print("Invoke not intended to be run directly, use for debugging only.")

    doc_pre(Context(), path="/dev")
