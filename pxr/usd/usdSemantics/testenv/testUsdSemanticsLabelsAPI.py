#!/pxrpythonsubst
#
# Copyright 2024 Pixar
#
# Licensed under the Apache License, Version 2.0 (the "Apache License")
# with the following modification; you may not use this file except in
# compliance with the Apache License and the following modification to it:
# Section 6. Trademarks. is deleted and replaced with:
#
# 6. Trademarks. This License does not grant permission to use the trade
#    names, trademarks, service marks, or product names of the Licensor
#    and its affiliates, except as required to comply with Section 4(c) of
#    the License and to reproduce the content of the NOTICE file.
#
# You may obtain a copy of the Apache License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Apache License with the above modification is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the Apache License for the specific
# language governing permissions and limitations under the Apache License.

import unittest

from pxr import Tf
from pxr import Gf
from pxr import Usd
from pxr import UsdSemantics

class TestPseudoRoot(unittest.TestCase):
    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()

    def testComputeOverInterval(self):
        pseudoRootSchema = UsdSemantics.LabelsAPI(
            self.stage.GetPseudoRoot(), "category")
        with self.assertRaises(Tf.ErrorException):
            pseudoRootSchema.ComputeOverInterval(Gf.Interval(0, 100))

    def testGetAppliedTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.GetDirectTaxonomies(
                self.stage.GetPseudoRoot()), [])

    def testComputeInheritedTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.ComputeInheritedTaxonomies(
                self.stage.GetPseudoRoot()),
            [])


class TestUnapplied(unittest.TestCase):
    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.rootPrim = self.stage.DefinePrim("/Bookcase")
        self.unappliedSchema = UsdSemantics.LabelsAPI(self.rootPrim, "style")
        self.assertFalse(self.unappliedSchema)

    def testComputeOverInterval(self):
        with self.assertRaises(Tf.ErrorException):
            self.unappliedSchema.ComputeOverInterval(Gf.Interval(0, 100))

    def testGetAppliedTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.GetDirectTaxonomies(self.rootPrim),
            [])

    def testComputeInheritedTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.ComputeInheritedTaxonomies(self.rootPrim),
            [])


class TestDirectlyApplied(unittest.TestCase):
    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.rootPrim = self.stage.DefinePrim("/Bookcase")
        self.appliedSemantics = \
            UsdSemantics.LabelsAPI.Apply(self.rootPrim, "style")
        self.appliedSemantics.GetLabelsAttr().Set(self.labels)
        self.assertFalse(
            self.appliedSemantics.GetLabelsAttr().ValueMightBeTimeVarying())

    def testGetAppliedTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.GetDirectTaxonomies(self.rootPrim),
            ["style"]
        )

    def testComputeInheritedTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.ComputeInheritedTaxonomies(self.rootPrim),
            ["style"]
        )

    def testComputeAncestorTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.ComputeAncestorTaxonomies(self.rootPrim),
            []
        )

    def testComputeOverIntervalBeforeFirstTimeSample(self):
        interval = Gf.Interval(-100, -50)
        labelsAttr = self.appliedSemantics.GetLabelsAttr()
        self.assertSequenceEqual(
            labelsAttr.GetTimeSamplesInInterval(interval), [])
        self.assertCountEqual(
            self.appliedSemantics.ComputeOverInterval(interval),
            self.timeSampledLabels[0])

    def testComputeOverIntervalAfterLastTimeSample(self):
        interval = Gf.Interval(200, 250)
        labelsAttr = self.appliedSemantics.GetLabelsAttr()
        self.assertSequenceEqual(
            labelsAttr.GetTimeSamplesInInterval(interval), [])
        self.assertCountEqual(
            self.appliedSemantics.ComputeOverInterval(interval),
            self.timeSampledLabels[150])

    def testComputeOverIntervalAroundLastTimeSamples(self):
        interval = Gf.Interval(125, 300)
        labelsAttr = self.appliedSemantics.GetLabelsAttr()
        self.assertCountEqual(
            labelsAttr.GetTimeSamplesInInterval(interval), [150])
        self.assertCountEqual(
            self.appliedSemantics.ComputeOverInterval(interval),
            set(self.timeSampledLabels[100]).union(self.timeSampledLabels[150]))

    def testComputeOverIntervalAroundALlTimeSamples(self):
        interval = Gf.Interval(-300, 300)
        labelsAttr = self.appliedSemantics.GetLabelsAttr()
        self.assertCountEqual(
            labelsAttr.GetTimeSamplesInInterval(interval), [0, 100, 150])
        self.assertCountEqual(
            self.appliedSemantics.ComputeOverInterval(interval),
            set(self.timeSampledLabels[0]).union(self.timeSampledLabels[100],
                                                 self.timeSampledLabels[150]))

class TestHierachy(unittest.TestCase):
    """Test helpers for computing ancestral taxonomies from the hierarchy

    The grandparent has two applications of the schema, the child has one,
    and the parent has zero.
    """
    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.grandparent = self.stage.DefinePrim("/Grandparent")
        self.parent = self.stage.DefinePrim("/Grandparent/Parent")
        self.child = self.stage.DefinePrim("/Grandparent/Parent/Child")

        UsdSemantics.LabelsAPI.Apply(self.grandparent, "style")
        UsdSemantics.LabelsAPI.Apply(self.parent, "category")
        UsdSemantics.LabelsAPI.Apply(self.child, "style")

    def testGetAppliedTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.GetDirectTaxonomies(self.grandparent),
            ["style"]
        )
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.GetDirectTaxonomies(self.parent),
            ["category"]
        )
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.GetDirectTaxonomies(self.child),
            ["style"]
        )

    def testComputeInheritedTaxonomies(self):
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.ComputeInheritedTaxonomies(self.grandparent),
            ["style"]
        )
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.ComputeInheritedTaxonomies(self.parent),
            ["style", "category"]
        )
        self.assertCountEqual(
            UsdSemantics.LabelsAPI.ComputeInheritedTaxonomies(self.child),
            ["style", "category"]
        )



if __name__ == "__main__":
    unittest.main()