
from __future__ import division

import os
import json
import re

from itertools import izip

import numpy as np

from . import tablewriter as tw

ZIP_FILETYPE = ".bz2"

__all__ = [
	"TableReader",
	]

class TableReaderError(Exception):
	"""
	Base exception class for TableReader-associated exceptions.
	"""
	pass


class NotUnzippedError(TableReaderError):
	"""
	An error raised when it appears that the input files are compressed.
	"""
	pass


class VersionError(TableReaderError):
	"""
	An error raised when the input files claim to be from a different version
	of the file specification.
	"""
	pass


class DoesNotExistError(TableReaderError):
	"""
	An error raised when a column or attribute does not seem to exist.
	"""
	pass


class VariableWidthError(TableReaderError):
	"""
	An error raised when trying to load an entire column as one array when
	entry sizes vary.
	"""
	pass


class TableReader(object):
	"""
	Reads output generated by TableWriter.

	Parameters
	----------
	path : str
		Path to the input location (a directory).

	See also
	--------
	wholecell.io.tablewriter.TableWriter

	Notes
	-----
	TODO (John): Consider a method for loading an indexed portion of a column.

	TODO (John): Consider removing unused methods (see below).

	TODO (John): Unit tests.

	"""

	def __init__(self, path):
		# Open version file for table
		versionFilePath = os.path.join(path, tw.DIR_METADATA, tw.FILE_VERSION)
		try:
			with open(versionFilePath) as f:
				version = f.read()

		except IOError as e:
			# Check if a zipped version file exists. Print appropriate error prompts.
			if os.path.exists(versionFilePath + ZIP_FILETYPE):
				raise NotUnzippedError("The version file for a table ({}) was found zipped. Unzip all table files before reading table.".format(path), e)
			else:
				raise VersionError("Could not open the version file for a table ({})".format(path), e)

		# Check if the table version matches the latest version
		if version != tw.VERSION:
			raise VersionError("Expected version {} but found version {}".format(tw.VERSION, version))

		# Read attribute names for table
		self._dirAttributes = os.path.join(path, tw.DIR_ATTRIBUTES)
		self._attributeNames = os.listdir(self._dirAttributes)

		# Read column names for table
		self._dirColumns = os.path.join(path, tw.DIR_COLUMNS)
		self._columnNames = os.listdir(self._dirColumns)


	def readAttribute(self, name):
		"""
		Load an attribute.

		Parameters
		----------
		name : str
			The name of the attribute.

		Returns
		-------
		The attribute, JSON-deserialized from a string.

		"""

		if name not in self._attributeNames:
			raise DoesNotExistError("No such attribute: {}".format(name))

		return json.loads(
			open(os.path.join(self._dirAttributes, name)).read()
			)


	def readColumn(self, name):
		"""
		Load a full column (all entries).

		Parameters
		----------
		name : str
			The name of the column.

		Returns
		-------
		A NumPy array, with entries along the first dimension.

		Notes
		-----
		If entry sizes varies, this method cannot be used.

		Output will be squeezed; e.g. scalars or scalar-likes written with
		TableWriter will be returned as vectors.

		TODO (John): Consider using np.memmap to defer loading of the data
			until it is operated on.  Early work (see issue #221) suggests that
			this may lead to cryptic performance issues.

		TODO (John): This method should probably use np.frombuffer rather than
			np.fromstring.  It seems that using np.fromstring here will become
			deprecated in later versions of NumPy.

		TODO (John): Open in binary mode.

		"""

		if name not in self._columnNames:
			raise DoesNotExistError("No such column: {}".format(name))

		offsets, dtype = self._loadOffsets(name)

		sizes = np.diff(offsets)

		if len(set(sizes)) > 1:
			raise VariableWidthError("Cannot load full column; data size varies")

		nEntries = sizes.size

		with open(os.path.join(self._dirColumns, name, tw.FILE_DATA)) as dataFile:
			dataFile.seek(offsets[0])

			return np.fromstring(
				dataFile.read(), dtype
				).reshape(nEntries, -1).squeeze()


	def iterColumn(self, name):
		"""
		Iterate over a column, entry-by-entry.

		Parameters
		----------
		name : str
			The name of the column.

		Yields
		------
		NumPy ndarrays.

		Notes
		-----
		TODO (John): This method appears to currently be unused.  Consider
			removing it.

		"""

		if name not in self._columnNames:
			raise DoesNotExistError("No such column: {}".format(name))

		offsets, dtype = self._loadOffsets(name)

		sizes = np.diff(offsets)

		with open(os.path.join(self._dirColumns, name, tw.FILE_DATA)) as dataFile:
			dataFile.seek(offsets[0])

			for size in sizes:
				yield np.fromstring(
					dataFile.read(size), dtype
					)


	def readRow(self, index):
		"""
		Returns the values for all columns for a given entry.

		Parameters
		----------
		index : int
			The index of the desired row (entry).

		Returns
		-------
		dict of {string: ndarray} pairs

		Notes
		-----
		TODO (John): This method appears to currently be unused.  Consider
			removing it.

		"""

		return {
			name: self._loadEntry(name, index)
			for name in self._columnNames
			}


	def _loadEntry(self, name, index):
		"""
		Internal method for loading a column value for a given entry.

		Parameters
		----------
		name : str
			Name of the column.
		index : int
			Index of the entry.

		Returns
		-------
		NumPy ndarray.

		"""

		offsets, dtype = self._loadOffsets(name)

		size = offsets[index+1] - offsets[index]

		with open(os.path.join(self._dirColumns, name, tw.FILE_DATA)) as dataFile:
			dataFile.seek(offsets[index])

			return np.fromstring(
				dataFile.read(size), dtype
				)


	def _loadOffsets(self, name):
		"""
		Internal method for loading data needed to interpret a column.

		Parameters
		----------
		name : str
			The name of the column.

		Returns
		-------
		offsets : ndarray (int)
			An integer array.  Each element corresponds to the offset (in
			bytes) for each entry in the column's data file.
		dtype : list-of-tuples-of-strings
			A data type specific for instantiating a NumPy ndarray.

		"""

		with open(os.path.join(self._dirColumns, name, tw.FILE_OFFSETS)) as offsetsFile:
			offsets = np.array([int(i.strip()) for i in offsetsFile])

		with open(os.path.join(self._dirColumns, name, tw.FILE_DATA)) as dataFile:
			rawDtype = json.loads(dataFile.read(offsets[0]))

			if isinstance(rawDtype, basestring):
				dtype = str(rawDtype)

			else:
				dtype = [ # numpy requires list-of-tuples-of-strings
					(str(n), str(t))
					for n, t in rawDtype
					]

		return offsets, dtype


	def attributeNames(self):
		"""
		Returns the names of all attributes.
		"""
		return self._attributeNames


	def columnNames(self):
		"""
		Returns the names of all columns.
		"""
		return self._columnNames


	def close(self):
		"""
		Does nothing.

		The TableReader keeps no files open, so this method does nothing.

		Notes
		-----
		TODO (John): Consider removing this method.  At the moment are usage is
			inconsistent, and gives the impression that it is actually
			beneficial or necessary.

		"""
		pass
