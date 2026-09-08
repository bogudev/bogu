from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..anonymizer.anonymizer import Anonymizer
from ..anonymizer.entity_map import EntityMap
from ..core.protocols import Detector

if TYPE_CHECKING:
    import pandas as pd


class DatasetAnonymizer:
    """
    Anonymizes pandas DataFrames or CSV files column-by-column.

    Requires: ``pip install bogu[adapters]``

    Parameters
    ----------
    detector:
        Any Detector-conforming object, including a PIIPipeline.
    """

    def __init__(self, detector: Detector) -> None:
        self._anon = Anonymizer(detector)

    def anonymize_dataframe(
        self,
        df: pd.DataFrame,
        *,
        columns: Sequence[str] | None = None,
        entity_map: EntityMap | None = None,
        inplace: bool = False,
    ) -> tuple[pd.DataFrame, EntityMap]:
        """
        Anonymize string columns in a DataFrame.

        Parameters
        ----------
        df:
            Input DataFrame.
        columns:
            Columns to anonymize. None → all ``object``-dtype columns.
        entity_map:
            Existing session map to extend.
        inplace:
            Modify df in place. Default False (returns a copy).

        Returns
        -------
        tuple[pd.DataFrame, EntityMap]
        """
        try:
            import pandas as pd  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "pandas is not installed.\n  pip install bogu[adapters]"
            ) from exc

        em = entity_map if entity_map is not None else EntityMap()
        result = df if inplace else df.copy()

        target_cols: list[str] = (
            list(columns)
            if columns is not None
            else list(result.select_dtypes(include=["object", "string"]).columns)
        )

        for col in target_cols:
            if col not in result.columns:
                raise ValueError(f"Column {col!r} not found in DataFrame.")
            result[col] = result[col].apply(
                lambda val, _em=em: (
                    self._anon.anonymize(str(val), entity_map=_em)[0]
                    if pd.notna(val)
                    else val
                )
            )

        return result, em

    def anonymize_csv(
        self,
        path: str,
        *,
        columns: Sequence[str] | None = None,
        entity_map: EntityMap | None = None,
    ) -> tuple[pd.DataFrame, EntityMap]:
        """
        Read a CSV file and anonymize it.

        Returns the anonymized DataFrame (does not write back to disk).
        """
        try:
            import pandas as pd  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "pandas is not installed.\n  pip install bogu[adapters]"
            ) from exc

        df = pd.read_csv(path)
        return self.anonymize_dataframe(df, columns=columns, entity_map=entity_map)
