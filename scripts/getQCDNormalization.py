#!/usr/bin/env python

import os
import sys
import optparse
import subprocess
from pprint import pprint

import ROOT
from ROOT import *


sys.path.append('../scripts/')
sys.path.append('scripts/')
import myRootFunctions as mRF

chandict = {'e':'e',
            'mu':'#mu'}


qcd_color = 2
mc_color = 3

def createDir(directory):
    from os import mkdir
    try:
        mkdir(directory)
    except OSError as exc:
        import errno, os.path
        if exc.errno == errno.EEXIST and os.path.isdir(directory):
            pass
        else: raise exc

    if not directory.endswith('/'): directory+='/'
    return directory

def getNormalization(i_file,chan,level,outputdir=''):

    postfix     = chan+'_'+level
    postfix_qcd = chan+'_antiiso_'+level

    # data  = mRF.getHist(i_file, chan+'/'+chan+'_'+level+'_data_0')
    data  = mRF.getHist(i_file,'data/'+postfix)
    data.SetMarkerStyle(20)
    data.GetXaxis().SetTitle('#slashed{E}_{T} [GeV]')

    qcd_shape_hist = mRF.getHist(i_file,'data/'+postfix_qcd) ## take the qcd templates from antiiso data

    # qcd   = mRF.getHist(i_file, chan+'/'+chan+'_'+level+'_qcd_0')
    qcd   = mRF.getHist(i_file,'QCD/'+postfix)
    qcd.SetLineWidth(2)
    qcd.SetLineColor(qcd_color)
    qcd.SetLineStyle(qcd_color)
    qcd.GetXaxis().SetTitle('#slashed{E}_{T} [GeV]')
    # wjets = mRF.getHist(i_file, chan+'/'+chan+'_'+level+'_wjets_0').Clone()
    # ttbar = mRF.getHist(i_file, chan+'/'+chan+'_'+level+'_ttbar_1725').Clone()
    # zjets = mRF.getHist(i_file, chan+'/'+chan+'_'+level+'_zjets_0').Clone()
    # stop  = mRF.getHist(i_file, chan+'/'+chan+'_'+level+'_singletop_0').Clone()
    wjets = mRF.getHist(i_file,'W+jets/'+postfix).Clone()
    ttbar = mRF.getHist(i_file,'t#bar{t}172.5/'+postfix).Clone()
    zjets = mRF.getHist(i_file,'Z#rightarrow ll/'+postfix).Clone()
    stop  = mRF.getHist(i_file,'Single top/'+postfix).Clone()
    vv    = mRF.getHist(i_file,'VV/'+postfix).Clone()

    mc = wjets.Clone('mc')
    mc.SetLineWidth(2)
    mc.SetLineColor(mc_color)
    mc.SetLineStyle(mc_color)
    mc.GetXaxis().SetTitle('#slashed{E}_{T} [GeV]')
    mc.Add(zjets)
    mc.Add(ttbar)
    mc.Add(stop)

    print 'Summary: ',level
    print '-'*25
    print 'ttbar     : %9.0f' % ttbar.Integral()
    print 'singletop : %9.0f' % stop.Integral()
    print 'wjets     : %9.0f' % wjets.Integral()
    print 'zjets     : %9.0f' % zjets.Integral()
    print '-'*25
    print 'mc sum    : %9.0f' % mc.Integral()
    print 'qcd       : %9.0f' % qcd.Integral()
    print '-'*25
    print 'data      : %9.0f' % data.Integral()
    print '-'*25

    frac_start = qcd.Integral(0, qcd.GetNbinsX()+1) / ( mc.Integral(0, mc.GetNbinsX()+1) + qcd.Integral(0, qcd.GetNbinsX()+1) )
    start = 0.2

    frac = RooRealVar('frac','frac',start,0.0,1.)
    met  = RooRealVar('met','met',0.,300.)
    data_shape = RooDataHist('data','data',          RooArgList(met),data)
    mc_shape   = RooDataHist('mc_shape','mc_shape',  RooArgList(met),mc)
    qcd_shape  = RooDataHist('qcd_shape','qcd_shape',RooArgList(met),qcd_shape_hist)

    mc_pdf  = RooHistPdf('mc_pdf' ,'mc_pdf' ,RooArgSet(met),mc_shape)
    qcd_pdf = RooHistPdf('qcd_pdf','qcd_pdf',RooArgSet(met),qcd_shape)


    model = RooAddPdf('model', 'model', RooArgList(qcd_pdf, mc_pdf), RooArgList(frac))
    model.fitTo(data_shape)


    c = TCanvas('qcd_'+chan,'qcd_'+chan,600,600)
    ROOT.gStyle.SetOptTitle(0)
    ROOT.gStyle.SetOptStat(0)
    frame = met.frame()
    data_shape.plotOn(frame,RooFit.Name('data'))
    model.plotOn(frame,RooFit.Name('model'))
    model.plotOn(frame,RooFit.Components('mc_pdf'),RooFit.LineStyle(mc_color),RooFit.LineColor(mc_color))
    model.plotOn(frame,RooFit.Components('qcd_pdf'),RooFit.LineStyle(qcd_color),RooFit.LineColor(qcd_color))
    c.SetLeftMargin(0.2)
    frame.GetXaxis().SetTitle('#slash{E}_{T} [GeV]')
    frame.GetYaxis().SetTitleOffset(2.5)
    frame.Draw()

    leg = TLegend(0.6,0.65,0.85,0.85)
    leg.SetFillColor(0)
    leg.SetLineColor(0)
    leg.SetHeader(chandict[chan]+'-Channel')
    leg.AddEntry(data,'Data','p')
    leg.AddEntry(mc,'t#bar{t},t,W+jets,DY','l')
    leg.AddEntry(qcd,'QCD','l')
    leg.Draw()

    pave = TPaveText(0.6,0.5,0.85,0.65,"NDC")
    pave.SetBorderSize(0)
    pave.SetFillStyle(0)
    # pave.SetTextAlign(32)
    # pave.SetTextFont(42)
    pave.AddText('f_{QCD} = %.3f' % frac.getVal()+' #pm %.3f ' % frac.getError())
    pave.AddText('#chi^{2}/N_{dof} = %.2f' % frame.chiSquare('model','data'))
    pave.AddText('SF = %.2f' % float(frac.getVal()/frac_start))
    pave.Draw()


    outdir = ''
    if len(outputdir)>0:
        outdir = createDir(outputdir)

    c.Update()
    c.Print(outdir+'qcd_'+chan+'_'+level+'.png')
    c.Print(outdir+'qcd_'+chan+'_'+level+'.pdf')
    # c.Print('qcd_'+chan+'_'+level+'.eps')
    # c.Print('qcd_'+chan+'_'+level+'.C')

    return float(frac.getVal()/frac_start),0.


def main():
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-i', '--inputfile',    dest='inputfile'   , help='Name of the input file containing the histograms.'             , default=None)
    parser.add_option('-b', '--batch',        dest='batch'       , help='Use this flag to run root in batch mode.', action='store_true' , default=False)
    parser.add_option('-q', '--qcdtemplates', dest='qcdtemplates', help='Name of the input file containing the QCD templates.'          , default=None)
    parser.add_option('-o', '--outputdir',    dest='outputdir'   , help='Name of the local output directory.'                           , default='QCDNormalization')
    (opt, args) = parser.parse_args()

    ## Handle input parameters:
    if opt.inputfile is None:
        parser.error('No input file defined!')
    inputfile = opt.inputfile

    if opt.batch:
        sys.argv.append( '-b' )
        ROOT.gROOT.SetBatch()

    i_file = mRF.openTFile(inputfile)

    channels = ['e','mu']
    print 'channels: ',channels
    # levels = set([k.split('_')[-1].replace('charge','met')   for k in mRF.GetKeyNames(i_file,'data') if 'charge' in k])
    levels = set([k.split('_',1)[-1].replace('charge','met') for k in mRF.GetKeyNames(i_file,'data') if 'charge' in k and not 'chargeCheck' in k and not len(k.split('_')) == 2])

    print 'levels: ',levels

    sfs = {}
    for chan in channels:
        # levels = [k.split('_')[1] for k in mRF.GetKeyNames(i_file,chan) if ('met' in k and not 'flow' in k)]
            for level in list(set(levels)):
                sf = getNormalization(i_file,chan,level,outputdir=opt.outputdir)
                sfs[chan+'_'+level] = sf



    pprint(sfs)
    ## write weights to a root file
    sf_hist = TH1F('qcdsf','qcdsf',len(sfs),0,len(sfs))
    i=0
    for l in sfs:
        i+=1
        sf_hist.GetXaxis().SetBinLabel(i,l)
        sf_hist.SetBinContent(i,sfs[l][0])
        sf_hist.SetBinError(i,sfs[l][1])
    sf_out = mRF.openTFile('data/weights/top_qcdsf.root','RECREATE')
    sf_hist.Write()
    sf_out.Close()



if __name__ == '__main__':
    main()
    print 'done'

