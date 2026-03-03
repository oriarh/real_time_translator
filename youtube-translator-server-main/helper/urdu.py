def urdu_transliterate(string, reverse=0):

    buck2uni = {
        "\u0627": "A",
        "\u0627": "A",
        "\u0675": "A",
        "\u0673": "A",
        "\u0630": "A",
        "\u0622": "AA",
        "\u0628": "B",
        "\u067E": "P",
        "\u062A": "T",
        "\u0637": "T",
        "\u0679": "T",
        "\u062C": "J",
        "\u0633": "S",
        "\u062B": "S",
        "\u0635": "S",
        "\u0686": "CH",
        "\u062D": "H",
        "\u0647": "H",
        "\u0629": "H",
        "\u06DF": "H",
        "\u062E": "KH",
        "\u062F": "D",
        "\u0688": "D",
        "\u0630": "Z",
        "\u0632": "Z",
        "\u0636": "Z",
        "\u0638": "Z",
        "\u068E": "Z",
        "\u0631": "R",
        "\u0691": "R",
        "\u0634": "SH",
        "\u063A": "GH",
        "\u0641": "F",
        "\u06A9": "K",
        "\u0642": "K",
        "\u06AF": "G",
        "\u0644": "L",
        "\u0645": "M",
        "\u0646": "N",
        "\u06BA": "N",
        "\u0648": "O",
        "\u0649": "Y",
        "\u0626": "Y",
        "\u06CC": "Y",
        "\u06D2": "E",
        "\u06C1": "H",
        "\u064A": "E",
        "\u06C2": "AH",
        "\u06BE": "H",
        "\u0639": "A",
        "\u0643": "K",
        "\u0621": "A",
        "\u0624": "O",
        "\u060C": "",  # seperator ulta comma
    }

    for k, v in buck2uni.items():
        if not reverse:
            string = string.replace(k, v)
        else:
            string = string.replace(v, k)

    return string
