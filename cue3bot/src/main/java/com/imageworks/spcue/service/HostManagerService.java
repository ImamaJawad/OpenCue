
/*
 * Copyright (c) 2018 Sony Pictures Imageworks Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */



package com.imageworks.spcue.service;

import java.sql.Timestamp;
import java.util.List;

import org.apache.log4j.Logger;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import com.imageworks.spcue.Allocation;
import com.imageworks.spcue.AllocationDetail;
import com.imageworks.spcue.DispatchHost;
import com.imageworks.spcue.EntityModificationError;
import com.imageworks.spcue.Frame;
import com.imageworks.spcue.Host;
import com.imageworks.spcue.HostDetail;
import com.imageworks.spcue.LocalHostAssignment;
import com.imageworks.spcue.Proc;
import com.imageworks.spcue.Show;
import com.imageworks.spcue.Source;
import com.imageworks.spcue.VirtualProc;
import com.imageworks.spcue.CueIce.HardwareState;
import com.imageworks.spcue.CueIce.HostTagType;
import com.imageworks.spcue.CueIce.LockState;
import com.imageworks.spcue.RqdIce.HostReport;
import com.imageworks.spcue.RqdIce.RenderHost;
import com.imageworks.spcue.dao.AllocationDao;
import com.imageworks.spcue.dao.FacilityDao;
import com.imageworks.spcue.dao.HostDao;
import com.imageworks.spcue.dao.ProcDao;
import com.imageworks.spcue.dao.ShowDao;
import com.imageworks.spcue.dao.SubscriptionDao;
import com.imageworks.spcue.dao.criteria.FrameSearch;
import com.imageworks.spcue.dao.criteria.ProcSearch;
import com.imageworks.spcue.iceclient.RqdClient;
import com.imageworks.spcue.iceclient.RqdClientException;

@Transactional
public class HostManagerService implements HostManager {
    private static final Logger logger = Logger.getLogger(HostManagerService.class);

    private HostDao hostDao;
    private RqdClient rqdClient;
    private ProcDao procDao;
    private ShowDao showDao;
    private FacilityDao facilityDao;
    private SubscriptionDao subscriptionDao;
    private AllocationDao allocationDao;

    public HostManagerService() { }

    @Override
    public void setHostLock(Host host, LockState lock, Source source) {
        hostDao.updateHostLock(host, lock, source);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public boolean isLocked(Host host) {
        return hostDao.isHostLocked(host);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public boolean isHostUp(Host host) {
        return hostDao.isHostUp(host);
    }

    @Override
    public void setHostState(Host host, HardwareState state) {
        hostDao.updateHostState(host, state);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public boolean isSwapping(Host host) {
        return hostDao.isKillMode(host);
    }

    public void rebootWhenIdle(Host host) {
        try {
            hostDao.updateHostState(host, HardwareState.RebootWhenIdle);
            rqdClient.rebootWhenIdle(host);
        }
        catch (RqdClientException e) {
            logger.info("failed to contact host: " + host.getName() + " for reboot");
        }
    }

    public void rebootNow(Host host) {
        try {
            hostDao.updateHostState(host, HardwareState.Rebooting);
            rqdClient.rebootNow(host);
        }
        catch (RqdClientException e) {
            logger.info("failed to contact host: " + host.getName() + " for reboot");
            hostDao.updateHostState(host, HardwareState.Down);
        }
    }

    @Override
    public void setHostStatistics(Host host,
            long totalMemory, long freeMemory,
            long totalSwap, long freeSwap,
            long totalMcp, long freeMcp,
            long totalGpu, long freeGpu,
            int load, Timestamp bootTime,
            String os) {

        hostDao.updateHostStats(host,
                totalMemory, freeMemory,
                totalSwap, freeSwap,
                totalMcp, freeMcp,
                totalGpu, freeGpu,
                load, bootTime, os);
    }

    @Transactional(propagation = Propagation.SUPPORTS, readOnly=true)
    public Host findHost(String name) {
        return hostDao.findHost(name);
    }

    @Transactional(propagation = Propagation.SUPPORTS, readOnly=true)
    public Host getHost(String id) {
        return hostDao.getHost(id);
    }

    @Transactional(propagation = Propagation.REQUIRED)
    public DispatchHost createHost(HostReport report) {
        return createHost(report.host);
    }

    @Transactional(propagation = Propagation.REQUIRED)
    public DispatchHost createHost(RenderHost rhost) {
        return createHost(rhost, getDefaultAllocationDetail());
    }

    @Transactional(propagation = Propagation.REQUIRED)
    public DispatchHost createHost(RenderHost rhost, AllocationDetail alloc) {

        hostDao.insertRenderHost(rhost, alloc);
        DispatchHost host = hostDao.findDispatchHost(rhost.name);

        hostDao.tagHost(host, alloc.tag, HostTagType.Alloc);
        hostDao.tagHost(host, host.name, HostTagType.Hostname);

        // Don't tag anything with hardware yet, we don't watch new procs
        // that report in to automatically start running frames.

        hostDao.recalcuateTags(host.id);
        return host;
    }

    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public DispatchHost findDispatchHost(String name) {
        return hostDao.findDispatchHost(name);
    }

    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public HostDetail findHostDetail(String name) {
        return hostDao.findHostDetail(name);
    }

    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public DispatchHost getDispatchHost(String id) {
        return hostDao.getDispatchHost(id);
    }

    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public HostDetail getHostDetail(Host host) {
        return hostDao.getHostDetail(host);
    }

    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public HostDetail getHostDetail(String id) {
        return hostDao.getHostDetail(id);
    }

    @Transactional(propagation = Propagation.SUPPORTS)
    public AllocationDetail getDefaultAllocationDetail() {
        return allocationDao.getDefaultAllocationDetail();
    }

    public void addTags(Host host, String[] tags) {
        for (String tag : tags) {
            if (tag == null) { continue; }
            if (tag.length() == 0) { continue; }
            hostDao.tagHost(host, tag, HostTagType.Manual);
        }
        hostDao.recalcuateTags(host.getHostId());
    }

    public void removeTags(Host host, String[] tags) {
        for (String tag: tags) {
            hostDao.removeTag(host, tag);
        }
        hostDao.recalcuateTags(host.getHostId());
    }

    public void renameTag(Host host, String oldTag, String newTag) {
        hostDao.renameTag(host, oldTag, newTag);
        hostDao.recalcuateTags(host.getHostId());
    }

    public void setAllocation(Host host, Allocation alloc) {

        if (procDao.findVirtualProcs(host).size() > 0) {
            throw new EntityModificationError("You cannot move hosts with " +
            		"running procs between allocations.");
        }

        hostDao.lockForUpdate(host);
        hostDao.updateHostSetAllocation(host, alloc);
        hostDao.recalcuateTags(host.getHostId());
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public int getStrandedCoreUnits(Host h) {
        return hostDao.getStrandedCoreUnits(h);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public boolean verifyRunningProc(String procId, String frameId) {
        return procDao.verifyRunningProc(procId, frameId);
    }

    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public List<VirtualProc> findVirtualProcs(FrameSearch request) {
        return procDao.findVirtualProcs(request);
    }

    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public VirtualProc findVirtualProc(Frame frame) {
        return procDao.findVirtualProc(frame);
    }

    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public List<VirtualProc> findVirtualProcs(HardwareState state) {
        return procDao.findVirtualProcs(state);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public List<VirtualProc> findVirtualProcs(LocalHostAssignment l) {
        return procDao.findVirtualProcs(l);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public List<VirtualProc> findVirtualProcs(ProcSearch r) {
        return procDao.findVirtualProcs(r);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public List<VirtualProc> findVirtualProcs(Host host) {
        return procDao.findVirtualProcs(host);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public List<VirtualProc> findBookedVirtualProcs(ProcSearch r) {
        return procDao.findBookedVirtualProcs(r);
    }

    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void unbookVirtualProcs(List<VirtualProc> procs) {
        for (VirtualProc proc: procs) {
            unbookProc(proc);
        }
    }

    @Transactional(propagation = Propagation.REQUIRED)
    public void unbookProc(Proc proc) {
        procDao.unbookProc(proc);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED)
    public void setHostResources(DispatchHost host, HostReport report) {
        hostDao.updateHostResources(host, report);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public VirtualProc getWorstMemoryOffender(Host h) {
        return procDao.getWorstMemoryOffender(h);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public VirtualProc getVirtualProc(String id) {
        return procDao.getVirtualProc(id);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public boolean isOprhan(Proc proc) {
        return procDao.isOrphan(proc);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public boolean isPreferShow(Host host) {
        return hostDao.isPreferShow(host);
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRED, readOnly=true)
    public Show getPreferredShow(Host host) {
        return showDao.getShowDetail(host);
    }

    public void deleteHost(Host host) {
        hostDao.deleteHost(host);
    }

    public AllocationDao getAllocationDao() {
        return allocationDao;
    }

    public void setAllocationDao(AllocationDao allocationDao) {
        this.allocationDao = allocationDao;
    }

    public HostDao getHostDao() {
        return hostDao;
    }

    public void setHostDao(HostDao hostDao) {
        this.hostDao = hostDao;
    }

    public ProcDao getProcDao() {
        return procDao;
    }

    public void setProcDao(ProcDao procDao) {
        this.procDao = procDao;
    }

    public RqdClient getRqdClient() {
        return rqdClient;
    }

    public void setRqdClient(RqdClient rqdClient) {
        this.rqdClient = rqdClient;
    }

    public FacilityDao getFacilityDao() {
        return facilityDao;
    }

    public void setFacilityDao(FacilityDao facilityDao) {
        this.facilityDao = facilityDao;
    }

    public ShowDao getShowDao() {
        return showDao;
    }

    public void setShowDao(ShowDao showDao) {
        this.showDao = showDao;
    }

    public SubscriptionDao getSubscriptionDao() {
        return subscriptionDao;
    }

    public void setSubscriptionDao(SubscriptionDao subscriptionDao) {
        this.subscriptionDao = subscriptionDao;
    }
}
