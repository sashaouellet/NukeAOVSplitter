from sdm import nodeUtils

nuke.menu('Nuke').addCommand('SDMTools/About', lambda: nuke.message('SDMTools is developed by Sasha Ouellet\nwww.sashaouellet.com'))
nuke.menu('Nodes').addCommand('SDMTools/Split AOVs', nodeUtils.splitAOVs, 'ctrl+alt+shift+s')
nuke.menu('Nodes').addCommand('SDMTools/Read Selected', nodeUtils.readSelected, 'shift+r')
nuke.menu('Nodes').addCommand('SDMTools/Reload Read Nodes', nodeUtils.reloadReads, 'alt+r')