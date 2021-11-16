from PySide2.QtWidgets import QWidget

from ...GUI.WDataExtractor.Ui_WDataExtractor import Ui_WDataExtractor
from PySide2.QtCore import Signal
from ...Functions.Plot import axes_dict, fft_dict
from ...Classes.Data import Data
from numpy import where
from numpy import argmin, abs as np_abs

type_extraction_dict = {
    "slice": "[",
    "slice (fft)": "[",
    "rms": "=rms",
    "rss": "=rss",
    "sum": "=sum",
    "mean": "=mean",
}


class WDataExtractor(Ui_WDataExtractor, QWidget):
    """Widget to define how to handle the 'non-plot' axis"""

    refreshNeeded = Signal()

    def __init__(self, parent=None):
        """Initialize the GUI according to info given by the WAxisManager widget

        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        parent : QWidget
            The parent QWidget
        """

        # Build the interface according to the .ui file
        QWidget.__init__(self, parent=parent)
        self.setupUi(self)
        self.name = "angle"
        self.axis = Data

        self.c_operation.currentTextChanged.connect(self.update_layout)
        self.slider.valueChanged.connect(self.update_floatEdit)
        self.lf_value.editingFinished.connect(self.update_slider)

    def get_operation_selected(self):
        """Method that return a string of the action selected by the user on the axis of the widget.
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object

        Output
        ---------
        string
            name of the current action selected
        """
        # Recovering the action selected by the user
        action_type = self.c_operation.currentText()

        # Formatting the string to have the right syntax
        if action_type in type_extraction_dict:
            if action_type == "slice":
                slice_index = self.slider.value()
                action = type_extraction_dict[action_type] + str(slice_index) + "]"

            elif action_type == "slice (fft)":
                slice_index = self.slider.value()
                action = type_extraction_dict[action_type] + str(slice_index) + "]"

                return fft_dict[self.axis.name] + action

            else:
                action = type_extraction_dict[action_type]

            return self.axis.name + action + "{" + self.unit + "}"

    def get_name(self):
        """Method that return the name of the axis of the WDataExtractor
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        """
        return self.name

    def set_name(self, name):
        """Method that set the name of the axis of the WDataExtractor
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        name : string
            string that hold the name of the axis
        """
        # Checking if the name of the axis is the name as the one displayed (z =/= axial direction for example)
        if name in axes_dict:
            self.in_name.setText(axes_dict[name])
        else:
            self.in_name.setText(name)

        self.name = name

    def set_operation(self, user_input):
        """Method that set the operation of the combobox of the WDataExtractor
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        user_input : list
            list of RequestedAxis that we use to set up the UI for the auto-plot
        """
        # Recovering the type of the operation and on which axis we are applying it
        operation_type = user_input.extension
        operation_name = user_input.name

        # Setting the label of the widget with the right name
        self.set_name(operation_name)

        # Converting type of the operation if we have a slice or a overlay/filter
        if operation_type == "single":
            operation_type = "slice"

        elif operation_type == "list":
            operation_type = "overlay/filter"

        # Setting operation combobox to the right operation
        self.c_operation.blockSignals(True)

        for i in range(self.c_operation.count()):
            self.c_operation.setCurrentIndex(i)

            if self.c_operation.currentText() == operation_type:
                break

        self.c_operation.blockSignals(False)
        self.update_layout()

        # Setting the slider to the right value if the operation is slice
        if operation_type == "slice":
            self.set_slider(user_input.indices[0])

    def set_slider(self, index):
        """Method that set the value of the slider of the WDataExtractor and then update floatEdit
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        index : int
            index at which the slider should be placed
        """
        self.slider.blockSignals(True)
        if index >= 0:
            self.slider.setValue(index)
        else:
            self.slider.setValue(self.slider.maximum() + index)
        self.slider.blockSignals(False)
        self.update_floatEdit()

    def set_slider_floatedit(self):
        """Method that set the value of the slider and the one of the floatEdit
        according to the axis sent by WAxisManager.
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        """
        # Converting the axis from rad to degree if the axis is angle as we do slice in degrees
        # Recovering the value from the axis as well
        if self.axis.name == "angle":
            self.axis_value = self.axis.get_values(unit="°")
            self.unit = "°"
        else:
            self.axis_value = self.axis.get_values()

        # Setting the initial value of the floatEdit to the minimum inside the axis
        self.lf_value.setValue(min(self.axis_value))

        # Setting the slider by giving the number of index according to the size of the axis
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.axis_value) - 1)

    def update(self, axis):
        """Method that will update the WDataExtractor widget according to the axis given to it
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        axis : string
            string with the name of the axis that should set the WDataExtractor widget
        """
        self.axis = axis
        self.unit = axis.unit
        self.set_name(axis.name)
        self.update_layout()
        self.set_slider_floatedit()

        # Depending on the axis we add or remove the slice (fft) operation
        self.c_operation.blockSignals(True)
        operation_list = list()
        for i in range(self.c_operation.count()):
            self.c_operation.setCurrentIndex(i)
            operation_list.append(self.c_operation.currentText())

        if "slice (fft)" in operation_list and not self.axis.name in fft_dict:
            operation_list.remove("slice (fft)")
        elif not "slice (fft)" in operation_list and self.axis.name in fft_dict:
            operation_list.insert(1, "slice (fft)")

        self.c_operation.clear()
        self.c_operation.addItems(operation_list)
        self.c_operation.blockSignals(False)

    def update_floatEdit(self):
        """Method that set the value of the floatEdit according to the value returned by the slider
        and the axis sent by WAxisManager.
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        """
        self.lf_value.blockSignals(True)
        self.lf_value.setValue(self.axis_value[self.slider.value()])
        self.lf_value.blockSignals(False)
        self.refreshNeeded.emit()

    def update_layout(self):
        """Method that update the layout of the WDataExtractor according to the extraction chosen
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        """
        # Recovering the operation selected
        extraction_selected = self.c_operation.currentText()

        # If the operation selected is a slice, then we show the slider and the floatEdit
        if extraction_selected == "slice" or extraction_selected == "slice (fft)":
            self.lf_value.show()
            self.slider.show()
            self.refreshNeeded.emit()
        else:
            self.lf_value.hide()
            self.slider.hide()

        # If the operation selected is overlay/filter then we show the related button
        if extraction_selected == "overlay/filter":
            self.b_action.show()
            self.b_action.setText(extraction_selected)
        else:
            self.b_action.hide()
            self.refreshNeeded.emit()

    def update_slider(self):
        """Method that set the value of the slider according to the value of the floatEdit
        according to the axis sent by WAxisManager.
        Parameters
        ----------
        self : WDataExtractor
            a WDataExtractor object
        """

        self.slider.blockSignals(True)
        # We set the value of the slider to the index closest to the value given
        index = argmin(np_abs(self.axis_value - self.lf_value.value()))
        self.slider.setValue(index)
        # We update the value of floatEdit to the index selected
        self.lf_value.setValue(self.axis_value[index])
        self.slider.blockSignals(False)
        self.refreshNeeded.emit()
