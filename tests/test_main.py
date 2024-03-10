import pytest

from niceplots import main


@pytest.mark.parametrize(
    "get_test_inputs_main",
    [
        ["test_main_barplots", "barplots"],
        ["test_main_lineplots", "lineplots"],
        ["test_main_histograms", "histograms"],
        ["test_main_all", "all"],
    ],
    indirect=["get_test_inputs_main"],
)
def test_main(get_test_inputs_main) -> None:
    name = get_test_inputs_main[0]
    prefix = get_test_inputs_main[1]
    config_path = get_test_inputs_main[2]
    codebook_path = get_test_inputs_main[3]
    data_path = get_test_inputs_main[4]
    plot_type = get_test_inputs_main[5]
    data_paths = (data_path,)

    input_args = (
        data_paths,
        codebook_path,
        config_path,
        name,
        plot_type,
        "pdf",
        False,
        "4",
        ("data",),
        prefix,
        False,
    )
    main.main(*input_args)
