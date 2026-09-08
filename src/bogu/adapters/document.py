from __future__ import annotations

import json
from pathlib import Path

from ..anonymizer.anonymizer import Anonymizer
from ..anonymizer.entity_map import EntityMap
from ..core.protocols import Detector
from ..policy import BoguPolicy
from ..preview import BoguPreview, create_preview

_SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".json"}


class DocumentAnonymizer:
    """
    Anonymizes entire documents in various formats.

    Supported formats: ``.txt``, ``.pdf``, ``.docx``, ``.json``

    Requires: ``pip install bogu[adapters]`` for PDF and DOCX support.

    Parameters
    ----------
    detector:
        Any Detector-conforming object, including a PIIPipeline.
    """

    def __init__(self, detector: Detector) -> None:
        self._detector = detector
        self._anon = Anonymizer(detector)

    def preview_file(
        self,
        path: str | Path,
        *,
        policy: BoguPolicy | None = None,
        entity_map: EntityMap | None = None,
    ) -> tuple[BoguPreview, EntityMap]:
        """Read and protect a document locally for review before transmission."""
        p = Path(path)
        suffix = p.suffix.lower()
        if suffix not in _SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: '{suffix}'. "
                f"Supported: {sorted(_SUPPORTED_EXTENSIONS)}"
            )
        return create_preview(
            self._read(p, suffix),
            self._detector,
            policy=policy,
            entity_map=entity_map,
        )

    def anonymize_file(
        self,
        path: str | Path,
        *,
        entity_map: EntityMap | None = None,
    ) -> tuple[str, EntityMap]:
        """
        Read the file, anonymize its text content.

        Does NOT write back to disk — the caller decides what to do with
        the anonymized text.

        Parameters
        ----------
        path:
            Path to the document.
        entity_map:
            Existing session map to extend for multi-document consistency.

        Returns
        -------
        tuple[str, EntityMap]
            ``(anonymized_text, entity_map)``
        """
        p = Path(path)
        suffix = p.suffix.lower()
        if suffix not in _SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: '{suffix}'. "
                f"Supported: {sorted(_SUPPORTED_EXTENSIONS)}"
            )
        text = self._read(p, suffix)
        return self._anon.anonymize(text, entity_map=entity_map)

    def _read(self, path: Path, suffix: str) -> str:
        if suffix == ".txt":
            return path.read_text(encoding="utf-8")
        if suffix == ".pdf":
            return self._read_pdf(path)
        if suffix == ".docx":
            return self._read_docx(path)
        if suffix == ".json":
            return self._read_json(path)
        raise AssertionError("unreachable")

    @staticmethod
    def _read_pdf(path: Path) -> str:
        try:
            import pdfplumber  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "pdfplumber is not installed.\n  pip install bogu[adapters]"
            ) from exc
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)

    @staticmethod
    def _read_docx(path: Path) -> str:
        try:
            import docx  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "python-docx is not installed.\n  pip install bogu[adapters]"
            ) from exc
        doc = docx.Document(str(path))
        return "\n".join(para.text for para in doc.paragraphs)

    @staticmethod
    def _read_json(path: Path) -> str:
        """Flatten JSON to indented text so all string values are exposed."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, indent=2, ensure_ascii=False)
