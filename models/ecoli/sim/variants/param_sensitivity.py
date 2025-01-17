'''
Used for sensitivity analysis on parameters from the fitter.  Increases one tenth
of parameters by a factor of 5 and decreases one tenth by 1/5 with 80% held constant.

Useful with variant analysis script param_sensitivity.py.

Modifies:
	sim_data.process.transcription.rnaData['KmEndoRNase']
	sim_data.process.translation.monomerData['degRate']
	sim_data.process.translation.translationEfficienciesByMonomer
	sim_data.process.transcription.rnaSynthProb: not actually used in sims
	sim_data.process.transcription.rnaExpression: used in initial_conditions
	sim_data.process.transcription_regulation.recruitmentData['hV']: used in initial_conditions and sims

Expected variant indices:
	0: control
	1+: modify random fraction of parameters
'''

from __future__ import division

import numpy as np

# Factor to scale each parameter by
# Increasing params will be *SCALE_FACTOR, decreasing will be /SCALE_FACTOR
SCALE_FACTOR = 5
# Factor to split the total number of parameters for increasing and decreasing
# For 100 params, SPLIT=5 would increase 20, decrease 20 and keep the rest constant
SPLIT = 10


def number_params(sim_data):
	'''
	Determines the number of parameters for each class of parameter that will
	be adjusted.

	Args:
		sim_data (SimulationData object)

	Returns:
		int: number of RNA degradation Km values
		int: number of protein degradation rates
		int: number of translation efficiencies
		int: number of synthesis probabilities
	'''

	n_rna_deg_rates = len(sim_data.process.transcription.rnaData['KmEndoRNase'])
	n_protein_deg_rates = len(sim_data.process.translation.monomerData['degRate'])
	n_translation_efficiencies = len(sim_data.process.translation.translationEfficienciesByMonomer)
	n_synth_prob = len(sim_data.process.transcription.rnaSynthProb
		[sim_data.process.transcription.rnaSynthProb.keys()[0]])

	return n_rna_deg_rates, n_protein_deg_rates, n_translation_efficiencies, n_synth_prob

def split_indices(sim_data, seed, split=SPLIT):
	'''
	Determine overall parameter indices to increase and decrease.

	Args:
		sim_data (SimulationData object)
		seed (int): numpy random seed (should be variant # to get different
			indices for each variant)
		split (float): factor to split the total number of parameters for
			increasing and decreasing. For 100 params, split=5 would
			increase 20 (100/5), decrease 20 (100/5) and keep the rest constant

	Returns:
		ndarray[int]: indices into total parameter array to increase parameter value
		ndarray[int]: indices into total parameter array to decrease parameter value
	'''

	total_params = np.sum(number_params(sim_data))
	param_split = total_params // split

	# Determine indices to change
	indices = np.arange(total_params)
	np.random.seed(seed)
	np.random.shuffle(indices)
	increase_indices = indices[:param_split]
	decrease_indices = indices[-param_split:]

	return increase_indices, decrease_indices

def param_indices(sim_data, indices):
	'''
	Get relative indices for individual parameter sets based on indices into
	the total number of parameters.

	Args:
		sim_data (SimulationData object)
		indices (ndarray[int]): indices for total parameter array

	Returns:
		ndarray[int]: indices for RNA degradation Km values that will change
		ndarray[int]: indices for protein degradation rates that will change
		ndarray[int]: indices for translation efficiencies that will change
		ndarray[int]: indices for synthesis probabilities that will change
	'''

	(n_rna_deg_rates,
		n_protein_deg_rates,
		n_translation_efficiencies,
		n_synth_prob) = number_params(sim_data)

	cutoff1 = n_rna_deg_rates
	cutoff2 = cutoff1 + n_protein_deg_rates
	cutoff3 = cutoff2 + n_translation_efficiencies

	rna_deg_indices = list(indices[np.where(indices < cutoff1)])
	protein_deg_indices = list(indices[np.where((indices >= cutoff1) & (indices < cutoff2))] - cutoff1)
	trans_eff_indices = list(indices[np.where((indices >= cutoff2) & (indices < cutoff3))] - cutoff2)
	synth_prob_indices = list(indices[np.where(indices >= cutoff3)] - cutoff3)

	return rna_deg_indices, protein_deg_indices, trans_eff_indices, synth_prob_indices

def modify_params(sim_data, indices, factor):
	'''
	Modify parameters in sim_data specified by indices (total parameter array)
	by a given factor.

	Args:
		sim_data (SimulationData object)
		indices (ndarray[int]): indices in the total parameter array to modify
		factor (float): factor to multiply by current parameter to get updated value
	'''

	(rna_deg_indices,
		protein_deg_indices,
		trans_eff_indices,
		synth_prob_indices) = param_indices(sim_data, indices)

	synth_prob_set = set(synth_prob_indices)
	recruitment_mask = np.array([hi in synth_prob_set for hi in sim_data.process.transcription_regulation.recruitmentData['hI']])

	sim_data.process.transcription.rnaData.struct_array['KmEndoRNase'][rna_deg_indices] *= factor
	sim_data.process.translation.monomerData.struct_array['degRate'][protein_deg_indices] *= factor
	sim_data.process.translation.translationEfficienciesByMonomer[trans_eff_indices] *= factor
	for synth_prob in sim_data.process.transcription.rnaSynthProb.values():
		synth_prob[synth_prob_indices] *= factor
	for exp in sim_data.process.transcription.rnaExpression.values():
		exp[synth_prob_indices] *= factor
	sim_data.process.transcription_regulation.recruitmentData['hV'][recruitment_mask] *= factor

def param_sensitivity_indices(sim_data):
	return 0

def param_sensitivity(sim_data, index):
	# No modifications for first index as control
	if index == 0:
		sim_data.increase_rna_deg_indices = []
		sim_data.increase_protein_deg_indices = []
		sim_data.increase_trans_eff_indices = []
		sim_data.increase_synth_prob_indices = []
		sim_data.decrease_rna_deg_indices = []
		sim_data.decrease_protein_deg_indices = []
		sim_data.decrease_trans_eff_indices = []
		sim_data.decrease_synth_prob_indices = []
		return dict(
			shortName = "control",
			desc = "Control simulation"
			), sim_data

	# Get number of params
	increase_indices, decrease_indices = split_indices(sim_data, index)

	# Update parameters
	# TODO kinetic params
	(sim_data.increase_rna_deg_indices,
		sim_data.increase_protein_deg_indices,
		sim_data.increase_trans_eff_indices,
		sim_data.increase_synth_prob_indices) = param_indices(sim_data, increase_indices)
	(sim_data.decrease_rna_deg_indices,
		sim_data.decrease_protein_deg_indices,
		sim_data.decrease_trans_eff_indices,
		sim_data.decrease_synth_prob_indices) = param_indices(sim_data, decrease_indices)

	modify_params(sim_data, increase_indices, SCALE_FACTOR)
	modify_params(sim_data, decrease_indices, 1 / SCALE_FACTOR)

	# Renormalize parameters
	for synth_prob in sim_data.process.transcription.rnaSynthProb.values():
		synth_prob /= synth_prob.sum()
	for exp in sim_data.process.transcription.rnaExpression.values():
		exp /= exp.sum()

	return dict(
		shortName="sensitivity_{}".format(index),
		desc="Simulation parameters adjusted, index: {}".format(index)
		), sim_data
