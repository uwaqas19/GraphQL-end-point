from __future__ import annotations
import os
from typing import Any, Dict, List
from graphql import GraphQLError

# Import the service module so we can look up whichever function name you have.
from app.services import wkt_clash_service as svc


class WKTClashQuery:


    @staticmethod
    def resolve_detect_plan_clashes(
        _parent,
        _info,
        filePath: str,
        aType: str,
        bType: str,
        zTolerance: float = 0.20,
        returnWkt: bool = False,
    ) -> List[Dict[str, Any]]:
        """detectPlanClashes(filePath, aType, bType, zTolerance=0.2, returnWkt=false)"""
        if not os.path.isfile(filePath):
            raise GraphQLError(f"File not found: {filePath}")

        # Support either service name: detect_plan_clashes or detectPlanClashes
        fn = getattr(svc, "detect_plan_clashes", None) or getattr(svc, "detectPlanClashes", None)
        if not callable(fn):
            raise GraphQLError("Server misconfig: wkt_clash_service is missing detect_plan_clashes")

        try:
            # Prefer keyword args (newer signature)
            return fn(filePath, aType, bType, z_tolerance=zTolerance, return_wkt=returnWkt)
        except TypeError:
            # Fall back to positional (older signature)
            return fn(filePath, aType, bType, zTolerance, returnWkt)

    @staticmethod
    def resolve_overlaps_2d_on_storey(
        _parent,
        _info,
        filePath: str,
        storeyId: str,
        aType: str,
        bType: str,
        zTolerance: float = 0.20,
        returnWkt: bool = False,
    ) -> List[Dict[str, Any]]:
        """overlaps2DOnStorey(filePath, storeyId, aType, bType, zTolerance=0.2, returnWkt=false)"""
        if not os.path.isfile(filePath):
            raise GraphQLError(f"File not found: {filePath}")

        # Support a few common function spellings in the service
        fn = (
            getattr(svc, "overlaps_2d_on_storey", None)
            or getattr(svc, "overlaps2d_on_storey", None)
            or getattr(svc, "overlaps2DOnStorey", None)
        )
        if not callable(fn):
            raise GraphQLError("Server misconfig: wkt_clash_service is missing overlaps_2d_on_storey")

        try:
            # Prefer keyword args (newer signature)
            return fn(
                filePath,
                storey_id=storeyId,
                a_type=aType,
                b_type=bType,
                z_tolerance=zTolerance,
                return_wkt=returnWkt,
            )
        except TypeError:
            # Fall back to positional (older signature)
            return fn(filePath, storeyId, aType, bType, zTolerance, returnWkt)
