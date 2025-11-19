import argparse
from pathlib import Path

import pytest

from opensafely import pull


project_fixture_path = Path(__file__).parent / "fixtures" / "projects"


def tag(image, version="v1"):
    return f"{pull.REGISTRY}/{image}:{version}"


def expect_local_images(run, stdout="", **kwargs):
    run.expect(
        [
            "docker",
            "images",
            "624658759468.dkr.ecr.ap-southeast-3.amazonaws.com/opensafely/*",
            "--filter",
            "label=org.opensafely.action",
            "--filter",
            "dangling=false",
            "--no-trunc",
            "--format={{.Repository}}:{{.Tag}}={{.ID}}",
        ],
        stdout=stdout,
        **kwargs,
    )


def test_default_no_local_images(run, capsys):
    run.expect(["docker", "info"])
    expect_local_images(run)

    pull.main(image="all", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.strip() == "No OpenSAFELY docker images found to update."


def test_default_no_local_images_force(run, capsys):
    run.expect(["docker", "info"])
    expect_local_images(run)
    # run.expect(["docker", "pull", tag("cohortextractor", version="latest")])
    run.expect(["docker", "pull", tag("ehrql")])
    run.expect(["docker", "pull", tag("jupyter")])
    run.expect(["docker", "pull", tag("python", version="v2")])
    run.expect(["docker", "pull", tag("r", version="v2")])
    run.expect(["docker", "pull", tag("rstudio", version="v2")])
    # run.expect(["docker", "pull", tag("sqlrunner")])
    # run.expect(["docker", "pull", tag("stata-mp")])
    run.expect(
        [
            "docker",
            "image",
            "prune",
            "--force",
            "--filter",
            "label=org.opencontainers.image.vendor=OpenSAFELY",
        ]
    )

    pull.main(image="all", force=True)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY ehrql:v1 image",
        "Updating OpenSAFELY jupyter:v1 image",
        "Updating OpenSAFELY python:v2 image",
        "Updating OpenSAFELY r:v2 image",
        "Updating OpenSAFELY rstudio:v2 image",
        "Pruning old OpenSAFELY docker images...",
    ]


def test_default_with_local_images(run, capsys):
    run.expect(["docker", "info"])
    expect_local_images(run, stdout="624658759468.dkr.ecr.ap-southeast-3.amazonaws.com/opensafely/r:v2=sha")
    run.expect(["docker", "pull", tag("r", version="v2")])
    run.expect(
        [
            "docker",
            "image",
            "prune",
            "--force",
            "--filter",
            "label=org.opencontainers.image.vendor=OpenSAFELY",
        ]
    )

    pull.main(image="all", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY r:v2 image",
        "Pruning old OpenSAFELY docker images...",
    ]


def test_default_with_old_docker(run, capsys):
    run.expect(["docker", "info"])
    expect_local_images(run, stdout="624658759468.dkr.ecr.ap-southeast-3.amazonaws.com/opensafely/r:<none>=sha")

    pull.main(image="all", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.strip() == "No OpenSAFELY docker images found to update."


def test_specific_image(run, capsys):
    run.expect(["docker", "info"])
    expect_local_images(run)
    run.expect(["docker", "pull", tag("r", version="v2")])
    run.expect(
        [
            "docker",
            "image",
            "prune",
            "--force",
            "--filter",
            "label=org.opencontainers.image.vendor=OpenSAFELY",
        ]
    )

    pull.main(image="r", force=False)
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY r:v2 image",
        "Pruning old OpenSAFELY docker images...",
    ]


def test_project(run, capsys):
    run.expect(["docker", "info"])
    expect_local_images(run)
    run.expect(["docker", "pull", tag("ehrql")])
    run.expect(["docker", "pull", tag("python", version="v2")])
    run.expect(
        [
            "docker",
            "image",
            "prune",
            "--force",
            "--filter",
            "label=org.opencontainers.image.vendor=OpenSAFELY",
        ]
    )

    pull.main(project=project_fixture_path / "project.yaml")
    out, err = capsys.readouterr()
    assert err == ""
    assert out.splitlines() == [
        "Updating OpenSAFELY ehrql:v1 image",
        "Updating OpenSAFELY python:v2 image",
        "Pruning old OpenSAFELY docker images...",
    ]

# NO NEED TO DELETE
# def test_remove_deprecated_images(run):
#     local_images = set(
#         [
#             "624658759468.dkr.ecr.ap-southeast-3.amazonaws.com/opensafely/r",
#         ]
#     )

#     run.expect(["docker", "image", "rm", "624658759468.dkr.ecr.ap-southeast-3.amazonaws.com/opensafely/r"])

#     pull.remove_deprecated_images(local_images)

# NO NEED TO DELETE
# def test_check_version_out_of_date(run):
#     expect_local_images(
#         run,
#         stdout="624658759468.dkr.ecr.ap-southeast-3.amazonaws.com/opensafely/python:v1=sha256:oldsha",
#     )
#     assert len(pull.check_version()) == 1


def test_check_version_up_to_date(run):
    current_sha = pull.get_remote_sha("624658759468.dkr.ecr.ap-southeast-3.amazonaws.com/opensafely/python", "latest")
    pull.token = None
    expect_local_images(
        run,
        stdout=f"624658759468.dkr.ecr.ap-southeast-3.amazonaws.com/opensafely/python:v1={current_sha}",
    )

    assert len(pull.check_version()) == 0


def test_get_actions_from_project_yaml_no_actions():
    path = project_fixture_path / "noactions.yaml"
    with pytest.raises(RuntimeError) as exc_info:
        pull.get_actions_from_project_file(path)

    assert "Invalid project.yaml" in str(exc_info.value)
    assert str(path) in str(exc_info.value)


@pytest.mark.parametrize(
    "argv,expected",
    [
        ([], dict(image="all", force=False, project=None)),
        (["--force"], dict(image="all", force=True, project=None)),
        (["r"], dict(image="r", force=False, project=None)),
        (["r", "--force"], dict(image="r", force=True, project=None)),
        (["--project"], dict(image="all", force=False, project="project.yaml")),
        (
            ["--project", "project.yaml"],
            dict(image="all", force=False, project="project.yaml"),
        ),
        (["invalid"], SystemExit()),
    ],
)
def test_pull_parser_valid(argv, expected, capsys):
    parser = argparse.ArgumentParser()
    pull.add_arguments(parser)
    if isinstance(expected, SystemExit):
        with pytest.raises(SystemExit):
            parser.parse_args(argv)
    else:
        assert parser.parse_args(argv) == argparse.Namespace(**expected)
