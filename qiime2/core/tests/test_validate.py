# ----------------------------------------------------------------------------
# Copyright (c) 2016-2021, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.core.exceptions import ValidationError, ImplementationError
import unittest
from qiime2.core.validate import ValidationObject
from qiime2.sdk import PluginManager
from qiime2.plugin.plugin import ValidatorRecord, Plugin
from qiime2.core.testing.type import (IntSequence1, AscIntSequence,
                                      Kennel, Dog, Squid, Octopus)
from qiime2.core.testing.format import IntSequenceFormat, Cephalapod


class TestValidationObject(unittest.TestCase):

    def setUp(self):
        self.simple_int_seq = IntSequenceFormat()

        with self.simple_int_seq.open() as fh:
            fh.write('\n'.join(map(str, range(3))))
        self.simple_int_seq.validate(level='max')

    def test_initialization(self):
        validator_object = ValidationObject(IntSequence1)

        self.assertEqual(validator_object.concrete_type, IntSequence1)

    def test_add_validator(self):

        def test_validator_method(data: list, level):
            pass

        test_record = ValidatorRecord(validator=test_validator_method,
                                      view=list, plugin='this_plugin',
                                      context=IntSequence1)

        validator_object = ValidationObject(IntSequence1)

        validator_object.add_validator(test_record)

        self.assertEqual(validator_object._validators,
                         [test_record])

    def test_add_validation_object(self):
        first_VO = ValidationObject(IntSequence1)
        second_VO = ValidationObject(IntSequence1)

        def first_validator(data: list, level):
            pass

        def second_validator(data: list, level):
            pass

        first_record = ValidatorRecord(validator=first_validator,
                                       view=list, plugin='this_plugin',
                                       context=IntSequence1)

        second_record = ValidatorRecord(validator=second_validator,
                                        view=list, plugin='this_plugin',
                                        context=IntSequence1)

        first_VO.add_validator(first_record)

        second_VO.add_validator(second_record)

        # Allows us to demonstrate add_validation_object sets _is_sorted to
        # false
        first_VO._sort_validators()

        first_VO.add_validation_object(second_VO)

        self.assertEqual(first_VO._validators, [first_record, second_record])
        self.assertFalse(first_VO._is_sorted)

    def test_catch_different_concrete_types(self):
        squid_vo = ValidationObject(Squid)
        octopus_vo = ValidationObject(Octopus)

        def squid_validator(data: Cephalapod, level):
            pass

        def octopus_validator(data: Cephalapod, level):
            pass

        squid_record = ValidatorRecord(validator=squid_validator,
                                       view=Cephalapod,
                                       plugin='ocean_plugin',
                                       context=Squid)

        octopus_record = ValidatorRecord(validator=octopus_validator,
                                         view=Cephalapod,
                                         plugin='sea_plugin',
                                         context=Octopus)

        squid_vo.add_validator(squid_record)
        octopus_vo.add_validator(octopus_record)

        with self.assertRaisesRegex(TypeError, "Unable to add"):
            squid_vo.add_validation_object(octopus_vo)

    def test_public_validators_generation(self):

        validator_object = ValidationObject(IntSequence1)

        def first_validator(data: list, level):
            pass

        def second_validator(data: list, level):
            pass

        first_record = ValidatorRecord(validator=first_validator,
                                       view=list, plugin='this_plugin',
                                       context=IntSequence1)

        second_record = ValidatorRecord(validator=second_validator,
                                        view=list, plugin='this_plugin',
                                        context=IntSequence1)

        validator_object.add_validator(first_record)
        validator_object.add_validator(second_record)

        self.assertEqual(validator_object.validators,
                         [first_record, second_record])
        self.assertTrue(validator_object._is_sorted)

    def test_run_validators(self):

        validator_object = ValidationObject(IntSequence1)

        has_run = False

        def test_validator_method(data: list, level):
            nonlocal has_run
            has_run = True
            self.assertEqual(data, [0, 1, 2])
            self.assertEqual(level, 'max')

        test_record = ValidatorRecord(validator=test_validator_method,
                                      view=list, plugin='this_plugin',
                                      context=IntSequence1)

        validator_object.add_validator(test_record)

        validator_object(self.simple_int_seq, level='max')

        self.assertTrue(has_run)

    def test_run_validators_validation_exception(self):
        validator_object = ValidationObject(AscIntSequence)

        def test_raising_validation_exception(data: list, level):
            raise ValidationError("2021-08-24")

        test_record = ValidatorRecord(
                          validator=test_raising_validation_exception,
                          view=list, plugin='this_plugin',
                          context=AscIntSequence)

        validator_object.add_validator(test_record)

        with self.assertRaisesRegex(ValidationError,
                                    "2021-08-24"):
            validator_object(data=[], level=None)

    def test_run_validators_unknown_exception(self):
        validator_object = ValidationObject(AscIntSequence)

        def test_raising_validation_exception(data: list, level):
            raise KeyError("2021-08-24")

        test_record = ValidatorRecord(
                          validator=test_raising_validation_exception,
                          view=list, plugin='this_plugin',
                          context=AscIntSequence)

        validator_object.add_validator(test_record)

        with self.assertRaisesRegex(ImplementationError,
                                    "attempted to validate"):
            validator_object(data=[], level=None)

    def test_validator_sorts(self):
        self.pm = PluginManager()

        test_object = self.pm.validators[Squid]

        self.assertFalse(test_object._is_sorted)

        exp = ['validator_sort_first',
               'validator_sort_middle',
               'validator_sort_middle_b',
               'validator_sort_last']

        exp2 = ['validator_sort_first',
                'validator_sort_middle_b',
                'validator_sort_middle',
                'validator_sort_last']

        obs = [record.validator.__name__ for record in test_object.validators]

        self.assertIn(obs, [exp, exp2])
        self.assertTrue(test_object._is_sorted)


class TestValidatorIntegration(unittest.TestCase):

    def setUp(self):

        # setup test plugin

        self.test_plugin = Plugin(name='validator_test_plugin',
                                  version='0.0.1',
                                  website='test.com',
                                  package='qiime2.core.tests',
                                  project_name='validator_test')

        self.pm = PluginManager()

        # setup test data
        self.simple_int_seq = IntSequenceFormat()

        with self.simple_int_seq.open() as fh:
            fh.write('\n'.join(map(str, range(3))))
        self.simple_int_seq.validate(level='max')

    def tearDown(self):
        # This is a deadman switch to ensure that the test_plugin has been
        # added
        self.assertIn(self.test_plugin.name, self.pm.plugins)
        self.pm.forget_singleton()

    def test_validator_from_each_type_in_expression(self):
        @self.test_plugin.register_validator(IntSequence1 | AscIntSequence)
        def blank_validator(data: list, level):
            pass

        self.pm.add_plugin(self.test_plugin)

    def test_no_transformer_available(self):
        @self.test_plugin.register_validator(IntSequence1 | Kennel[Dog])
        def blank_validator(data: list, level):
            pass

        with self.assertRaisesRegex(
                AssertionError,
                r"Kennel\[Dog\].*blank_validator.*transform.*builtins:list"):
            self.pm.add_plugin(self.test_plugin)


class TestValidatorRegistration(unittest.TestCase):

    def setUp(self):

        self.test_plugin = Plugin(name='validator_test_plugin',
                                  version='0.0.1',
                                  website='test.com',
                                  package='qiime2.core.tests',
                                  project_name='validator_test')

    def test_catch_missing_validator_arg(self):

        run_checker = False

        with self.assertRaisesRegex(TypeError, "does not contain the"
                                    " required arguments"):
            run_checker = True

            @self.test_plugin.register_validator(IntSequence1)
            def validator_missing_level(data: list):
                pass

        assert run_checker

    def test_catch_extra_validator_arg(self):

        run_checker = False

        with self.assertRaisesRegex(TypeError, "does not contain the"
                                    " required arguments"):
            run_checker = True

            @self.test_plugin.register_validator(IntSequence1)
            def validator_extra_arg(data: list, level, spleen):
                pass

        assert run_checker

    def test_catch_no_data_annotation_in_validator(self):
        run_checker = False

        with self.assertRaisesRegex(TypeError, "No expected view type"
                                    " provided as annotation for `data`"
                                    " variable"):
            run_checker = True

            @self.test_plugin.register_validator(IntSequence1)
            def validator_no_view_annotation(data, level):
                pass

        assert run_checker
