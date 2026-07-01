from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import (
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
    MinMaxScaler,
    RobustScaler
)


def build_preprocessor(
    X,
    missing_strategy,
    encoding_strategy,
    scaling_strategy
):
    """
    Build the preprocessing pipeline.

    The returned ColumnTransformer is fitted only
    on the training data through an sklearn Pipeline,
    preventing data leakage.
    """

    # --------------------------------------------------
    # Detect Feature Types
    # --------------------------------------------------

    numeric_features = list(
        X.select_dtypes(
            include="number"
        ).columns
    )

    categorical_features = list(
        X.select_dtypes(
            include=[
                "object",
                "category",
                "bool"
            ]
        ).columns
    )

    # --------------------------------------------------
    # Missing Value Handling
    # --------------------------------------------------

    if missing_strategy == "None":

        numeric_imputer = "passthrough"
        categorical_imputer = "passthrough"

    elif missing_strategy == "Mean":

        numeric_imputer = SimpleImputer(
            strategy="mean"
        )

        categorical_imputer = SimpleImputer(
            strategy="most_frequent"
        )

    elif missing_strategy == "Median":

        numeric_imputer = SimpleImputer(
            strategy="median"
        )

        categorical_imputer = SimpleImputer(
            strategy="most_frequent"
        )

    elif missing_strategy == "Most Frequent":

        numeric_imputer = SimpleImputer(
            strategy="most_frequent"
        )

        categorical_imputer = SimpleImputer(
            strategy="most_frequent"
        )

    elif missing_strategy == "Drop Rows":

        raise ValueError(
            "Drop Rows must be handled before "
            "building the preprocessing pipeline."
        )

    else:

        raise ValueError(
            "Invalid missing value strategy."
        )

    # --------------------------------------------------
    # Encoding
    # --------------------------------------------------

    if encoding_strategy == "None":

        encoder = "passthrough"

    elif encoding_strategy == "One-Hot":

        encoder = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False
        )

    elif encoding_strategy == "Ordinal":

        encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1
        )

    else:

        raise ValueError(
            "Invalid encoding strategy."
        )

    # --------------------------------------------------
    # Scaling
    # --------------------------------------------------

    if scaling_strategy == "None":

        scaler = "passthrough"

    elif scaling_strategy == "StandardScaler":

        scaler = StandardScaler()

    elif scaling_strategy == "MinMaxScaler":

        scaler = MinMaxScaler()

    elif scaling_strategy == "RobustScaler":

        scaler = RobustScaler()

    else:

        raise ValueError(
            "Invalid scaling strategy."
        )
    
    # --------------------------------------------------
    # Numeric Pipeline
    # --------------------------------------------------

    numeric_pipeline = Pipeline(

        steps=[

            (
                "imputer",
                numeric_imputer
            ),

            (
                "scaler",
                scaler
            )

        ]

    )

    # --------------------------------------------------
    # Categorical Pipeline
    # --------------------------------------------------

    categorical_pipeline = Pipeline(

        steps=[

            (
                "imputer",
                categorical_imputer
            ),

            (
                "encoder",
                encoder
            )

        ]

    )

    # --------------------------------------------------
    # Column Transformer
    # --------------------------------------------------

    preprocessor = ColumnTransformer(

        transformers=[

            (

                "numeric",

                numeric_pipeline,

                numeric_features

            ),

            (

                "categorical",

                categorical_pipeline,

                categorical_features

            )

        ],

        remainder="drop",

        verbose_feature_names_out=False

    )

    return preprocessor